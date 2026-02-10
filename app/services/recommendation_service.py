import logging
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from app.models.models import Recommendation, Student
from app.utils.class_utils import get_major_code
from app.db.redis import cache_get, cache_set, make_hash_key
from app.schemas.dtos import (
    RecFilterDTO, RecOptionsDTO, RecItemDTO,
    RecSummaryDTO, RecListResponseDTO,
)

REC_OPTIONS_TTL = 21600  # 6h
REC_LIST_TTL = 21600     # 6h

logger = logging.getLogger(__name__)


class RecommendationService:
    @staticmethod
    def get_options(db: Session, year: Optional[int], college: Optional[str]) -> RecOptionsDTO:
        key = make_hash_key("rec_opts", year=year, college=college)
        cached = cache_get(key)
        if cached is not None:
            return RecOptionsDTO(**cached)

        years = [r[0] for r in db.query(distinct(Recommendation.year)).order_by(Recommendation.year.desc()).all()]

        q = db.query(distinct(Recommendation.college)).order_by(Recommendation.college)
        if year:
            q = q.filter(Recommendation.year == year)
        colleges = [r[0] for r in q.all()]

        q = db.query(distinct(Recommendation.major)).order_by(Recommendation.major)
        if year:
            q = q.filter(Recommendation.year == year)
        if college:
            q = q.filter(Recommendation.college == college)
        majors = [r[0] for r in q.all()]

        result = RecOptionsDTO(years=years, colleges=colleges, majors=majors)
        cache_set(key, result.model_dump(), REC_OPTIONS_TTL)
        return result

    @staticmethod
    def query_list(db: Session, f: RecFilterDTO) -> RecListResponseDTO:
        key = make_hash_key("rec_list",
            year=f.year, college=f.college, major=f.major,
            page=f.page, pageSize=f.pageSize)
        cached = cache_get(key)
        if cached is not None:
            return RecListResponseDTO(**cached)

        q = db.query(Recommendation).filter(Recommendation.year == f.year)
        if f.college:
            q = q.filter(Recommendation.college == f.college)
        if f.major:
            q = q.filter(Recommendation.major == f.major)

        total = q.count()
        if total == 0:
            empty = RecListResponseDTO(
                summary=RecSummaryDTO(recommended=0),
                list=[], total=0, page=f.page, pageSize=f.pageSize,
            )
            cache_set(key, empty.model_dump(), REC_LIST_TTL)
            return empty

        if f.major:
            q = q.order_by(Recommendation.compRank)
        else:
            q = q.order_by(Recommendation.college, Recommendation.major, Recommendation.compRank)

        # Paginate
        offset = (f.page - 1) * f.pageSize
        recs: List[Recommendation] = q.offset(offset).limit(f.pageSize).all()

        # Batch fetch student info for GPA and rank
        sids = [r.studentId for r in recs]
        stu_map: Dict[str, Student] = {}
        for i in range(0, len(sids), 500):
            batch = sids[i:i + 500]
            students = db.query(Student).filter(Student.studentId.in_(batch)).all()
            for s in students:
                stu_map[s.studentId] = s

        # Build items
        items: List[RecItemDTO] = []
        for r in recs:
            stu = stu_map.get(r.studentId)
            items.append(RecItemDTO(
                college=r.college,
                major=r.major,
                recGpa=r.courseGpa,
                latestGpa=round(stu.sGpa, 2) if stu and stu.sGpa is not None else None,
                perfScore=r.perfScore,
                compScore=r.compScore,
                compRank=r.compRank,
                latestGpaRank=stu.majorGpaRank if stu else None,
                remark=r.remark or '',
            ))

        # Summary (based on total, not page)
        major_total = RecommendationService._calc_major_total(db, f, recs, stu_map)
        rate = None
        if major_total is not None and major_total > 0:
            rate = f"{(total / major_total * 100):.1f}%"

        result = RecListResponseDTO(
            summary=RecSummaryDTO(
                recommended=total,
                majorTotal=major_total,
                rate=rate,
            ),
            list=items,
            total=total,
            page=f.page,
            pageSize=f.pageSize,
        )
        cache_set(key, result.model_dump(), REC_LIST_TTL)
        return result

    @staticmethod
    def _calc_major_total(db: Session, f: RecFilterDTO, recs: List[Recommendation],
                          stu_map: Dict[str, Student]) -> Optional[int]:
        """Calculate total students for the filter condition.
        Uses s_class prefix (major_code) to identify majors, consistent with project convention."""
        # If major is specified and major_total is available, use it directly
        if f.major:
            mt = recs[0].majorTotal if recs and recs[0].majorTotal is not None else None
            if mt is not None:
                return mt
            # Fallback: find major_code from stu_map, then count by s_class prefix
            major_code = None
            for r in recs:
                stu = stu_map.get(r.studentId)
                if stu and stu.sClass:
                    major_code = get_major_code(stu.sClass)
                    break
            if major_code:
                count = db.query(func.count(Student.studentId)).filter(
                    Student.sClass.like(f"{major_code}%")
                ).scalar()
                return count if count else None
            return None

        # If only college or only year: count from student table by grade
        grade = None
        for stu in stu_map.values():
            if stu.sGrade:
                grade = stu.sGrade
                break
        if grade:
            q = db.query(func.count(Student.studentId)).filter(Student.sGrade == grade)
            if f.college:
                q = q.filter(Student.sCollege == f.college)
            count = q.scalar()
            return count if count else None

        return None
