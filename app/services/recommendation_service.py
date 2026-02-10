import logging
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from app.models.models import Recommendation, Student
from app.utils.class_utils import get_major_code
from app.schemas.dtos import (
    RecFilterDTO, RecOptionsDTO, RecItemDTO,
    RecSummaryDTO, RecListResponseDTO,
)

logger = logging.getLogger(__name__)


class RecommendationService:
    @staticmethod
    def get_options(db: Session, year: Optional[int], college: Optional[str]) -> RecOptionsDTO:
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

        return RecOptionsDTO(years=years, colleges=colleges, majors=majors)

    @staticmethod
    def query_list(db: Session, f: RecFilterDTO) -> RecListResponseDTO:
        q = db.query(Recommendation).filter(Recommendation.year == f.year)
        if f.college:
            q = q.filter(Recommendation.college == f.college)
        if f.major:
            q = q.filter(Recommendation.major == f.major)

        if f.major:
            recs: List[Recommendation] = q.order_by(Recommendation.compRank).all()
        else:
            recs: List[Recommendation] = q.order_by(
                Recommendation.college, Recommendation.major, Recommendation.compRank
            ).all()
        if not recs:
            return RecListResponseDTO(
                summary=RecSummaryDTO(recommended=0),
                list=[]
            )

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

        # Summary
        recommended = len(recs)
        major_total = RecommendationService._calc_major_total(db, f, recs, stu_map)
        rate = None
        if major_total is not None and major_total > 0:
            rate = f"{(recommended / major_total * 100):.1f}%"

        return RecListResponseDTO(
            summary=RecSummaryDTO(
                recommended=recommended,
                majorTotal=major_total,
                rate=rate,
            ),
            list=items,
        )

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
