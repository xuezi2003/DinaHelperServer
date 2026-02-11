from types import SimpleNamespace
from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_
from app.models.models import Student, CourseScore
from app.schemas.dtos import CourseInfoFilterDTO
from app.utils.class_utils import get_major_code
from app.db.redis import cache_get, cache_set, make_hash_key
from typing import List, Dict, Any, Optional

STUDENT_TTL = 3600
SCORES_TTL = 3600
RANKING_TTL = 3600
MAJOR_RANKING_TTL = 3600
COURSE_NAMES_TTL = 21600
FAIL_RATE_TTL = 3600
FILTER_OPTIONS_TTL = 3600

def _student_to_dict(s: Student) -> dict:
    return {
        "studentId": s.studentId, "sName": s.sName, "sPy": s.sPy,
        "sCollege": s.sCollege, "sMajor": s.sMajor, "sGrade": s.sGrade,
        "sClass": s.sClass, "sAvg": s.sAvg, "sGpa": s.sGpa,
        "classAvgRank": s.classAvgRank, "classGpaRank": s.classGpaRank,
        "majorAvgRank": s.majorAvgRank, "majorGpaRank": s.majorGpaRank,
    }

def _dict_to_student_ns(d: dict) -> SimpleNamespace:
    return SimpleNamespace(**d)

def _course_to_dict(c: CourseScore) -> dict:
    return {
        "studentId": c.studentId, "cTerm": c.cTerm, "courseName": c.courseName,
        "score": c.score, "cType": c.cType, "cHours": c.cHours,
        "cCredit": c.cCredit, "cPass": c.cPass,
    }

class StudentRepository:
    @staticmethod
    def get_by_id(db: Session, student_id: str) -> Optional[Any]:
        key = f"student:{student_id}"
        cached = cache_get(key)
        if cached is not None:
            return _dict_to_student_ns(cached)
        student = db.query(Student).filter(Student.studentId == student_id).first()
        if student:
            cache_set(key, _student_to_dict(student), STUDENT_TTL)
        return student

    @staticmethod
    def get_ranking(db: Session, student_id: str, scope: str = 'class') -> Dict[str, int]:
        """从数据库获取预计算的排名和总人数。"""
        key = f"rank:{student_id}:{scope}"
        cached = cache_get(key)
        if cached is not None:
            return cached

        student = db.query(Student).filter(Student.studentId == student_id).first()
        if not student:
            return {"avg_rank": 0, "gpa_rank": 0, "total": 0}
            
        if scope == 'class':
            total = db.query(func.count(Student.studentId)).filter(Student.sClass == student.sClass).scalar()
            result = {
                "avg_rank": student.classAvgRank or 0, 
                "gpa_rank": student.classGpaRank or 0,
                "total": total or 0
            }
        else:
            major_code = get_major_code(student.sClass)
            total = db.query(func.count(Student.studentId)).filter(Student.sClass.like(f"{major_code}%")).scalar()
            result = {
                "avg_rank": student.majorAvgRank or 0, 
                "gpa_rank": student.majorGpaRank or 0,
                "total": total or 0
            }
        cache_set(key, result, RANKING_TTL)
        return result

    @staticmethod
    def get_by_pinyin(db: Session, pinyin: str) -> List[Student]:
        return db.query(Student).filter(Student.sPy == pinyin).order_by(Student.studentId).all()
    
    @staticmethod
    def get_by_name(db: Session, name: str) -> List[Student]:
        return db.query(Student).filter(Student.sName == name).order_by(Student.studentId).all()
    
    @staticmethod
    def get_major_ranking(db: Session, major_code: str, sort_by: str = 'gpa', order: str = 'desc') -> List[Any]:
        """获取专业内所有学生，按绩点或均分排序。
        major_code 为 s_class 前 8 位。"""
        key = f"major_ranking:{major_code}:{sort_by}:{order}"
        cached = cache_get(key)
        if cached is not None:
            return [_dict_to_student_ns(d) for d in cached]

        query = db.query(Student).filter(Student.sClass.like(f"{major_code}%"))
        
        if sort_by == 'gpa':
            sort_column = Student.sGpa
        else:
            sort_column = Student.sAvg
            
        if order == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        students = query.all()
        cache_set(key, [_student_to_dict(s) for s in students], MAJOR_RANKING_TTL)
        return students

class CourseScoreRepository:
    @staticmethod
    def get_by_student_id(db: Session, student_id: str) -> List[Any]:
        key = f"scores:{student_id}"
        cached = cache_get(key)
        if cached is not None:
            return [SimpleNamespace(**d) for d in cached]
        scores = db.query(CourseScore).filter(CourseScore.studentId == student_id).all()
        if scores:
            cache_set(key, [_course_to_dict(c) for c in scores], SCORES_TTL)
        return scores
    
    @staticmethod
    def get_course_names(db: Session, course_name: str) -> List[str]:
        key = f"course_names:{course_name}"
        cached = cache_get(key)
        if cached is not None:
            return cached
        query = db.query(CourseScore.courseName).distinct()
        if course_name:
            safe_name = course_name.replace('%', '\\%').replace('_', '\\_')
            query = query.filter(CourseScore.courseName.like(f"%{safe_name}%"))
        names = [row[0] for row in query.order_by(CourseScore.courseName).all()]
        cache_set(key, names, COURSE_NAMES_TTL)
        return names

    @staticmethod
    def get_fail_rate_statis(db: Session, filter_dto: CourseInfoFilterDTO) -> Dict[str, Any]:
        key = make_hash_key("fail_rate",
            courseName=filter_dto.courseName, terms=filter_dto.terms,
            colleges=filter_dto.colleges, majors=filter_dto.majors, classes=filter_dto.classes)
        cached = cache_get(key)
        if cached is not None:
            return cached

        subq = db.query(
            CourseScore.studentId,
            CourseScore.courseName,
            func.max(CourseScore.cPass).label("final_pass_status"),
            func.max(CourseScore.score).label("final_score")
        ).join(Student, CourseScore.studentId == Student.studentId)
        
        if filter_dto.courseName:
            subq = subq.filter(CourseScore.courseName == filter_dto.courseName)
        if filter_dto.terms:
            subq = subq.filter(CourseScore.cTerm.in_(filter_dto.terms))
        if filter_dto.colleges:
            subq = subq.filter(Student.sCollege.in_(filter_dto.colleges))
        if filter_dto.majors:
            subq = subq.filter(Student.sMajor.in_(filter_dto.majors))
        if filter_dto.classes:
            subq = subq.filter(Student.sClass.in_(filter_dto.classes))
            
        subq = subq.group_by(CourseScore.studentId, CourseScore.courseName).subquery()
        
        from sqlalchemy import or_
        stats = db.query(
            func.count(func.distinct(subq.c.studentId)).label("totalStudents"),
            func.sum(case((or_(subq.c.final_pass_status.in_([1, 2]), subq.c.final_score < 60), 1), else_=0)).label("failStudents"),
            func.sum(case((and_(subq.c.final_score >= 0, subq.c.final_score < 60), 1), else_=0)).label("0-59"),
            func.sum(case((and_(subq.c.final_score >= 60, subq.c.final_score < 70), 1), else_=0)).label("60-69"),
            func.sum(case((and_(subq.c.final_score >= 70, subq.c.final_score < 80), 1), else_=0)).label("70-79"),
            func.sum(case((and_(subq.c.final_score >= 80, subq.c.final_score < 90), 1), else_=0)).label("80-89"),
            func.sum(case((subq.c.final_score >= 90, 1), else_=0)).label("90-100")
        ).first()
        
        if not stats or stats.totalStudents == 0:
            return {
                "totalStudents": 0, "failStudents": 0,
                "0-59": 0, "60-69": 0, "70-79": 0, "80-89": 0, "90-100": 0
            }
            
        result = {k: int(v) for k, v in zip(stats._fields, stats)}
        cache_set(key, result, FAIL_RATE_TTL)
        return result

    @staticmethod
    def get_available_options(db: Session, filter_dto: CourseInfoFilterDTO, field: str) -> List[str]:
        """动态获取可用的筛选选项。
        field 可选值: 'c_term', 's_college', 's_major', 's_class'。"""
        key = make_hash_key(f"filter_opts:{field}",
            courseName=filter_dto.courseName, terms=filter_dto.terms,
            colleges=filter_dto.colleges, majors=filter_dto.majors, classes=filter_dto.classes)
        cached = cache_get(key)
        if cached is not None:
            return cached
        field_mapping = {
            'c_term': (CourseScore, 'cTerm'),
            's_college': (Student, 'sCollege'),
            's_major': (Student, 'sMajor'),
            's_class': (Student, 'sClass'),
        }
        
        if field not in field_mapping:
            return []
        
        model_class, attr_name = field_mapping[field]
        model_attr = getattr(model_class, attr_name)
        
        query = db.query(model_attr).distinct()
        query = query.join(CourseScore, CourseScore.studentId == Student.studentId) if model_class == Student else query.join(Student, CourseScore.studentId == Student.studentId)
        
        if filter_dto.courseName:
            query = query.filter(CourseScore.courseName == filter_dto.courseName)
        if field != 'c_term' and filter_dto.terms:
            query = query.filter(CourseScore.cTerm.in_(filter_dto.terms))
        if field != 's_college' and filter_dto.colleges:
            query = query.filter(Student.sCollege.in_(filter_dto.colleges))
        if field != 's_major' and filter_dto.majors:
            query = query.filter(Student.sMajor.in_(filter_dto.majors))
        if field != 's_class' and filter_dto.classes:
            query = query.filter(Student.sClass.in_(filter_dto.classes))
            
        query = query.filter(Student.studentId.isnot(None))
        if model_class == Student:
            query = query.filter(model_attr.isnot(None), model_attr != '')
            
        options = [row[0] for row in query.order_by(model_attr).all()]
        cache_set(key, options, FILTER_OPTIONS_TTL)
        return options

