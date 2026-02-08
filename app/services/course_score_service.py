from sqlalchemy.orm import Session
from app.services.repositories import CourseScoreRepository
from app.models.models import CourseScore
from app.schemas.dtos import CourseInfoFilterDTO, FailRateStatisDTO
from typing import List

class CourseScoreService:
    @staticmethod
    def get_scores_by_student_id(db: Session, student_id: str) -> List[CourseScore]:
        return CourseScoreRepository.get_by_student_id(db, student_id)

    @staticmethod
    def get_fail_rate_statistics(db: Session, filter_dto: CourseInfoFilterDTO) -> FailRateStatisDTO:
        stats_map = CourseScoreRepository.get_fail_rate_statis(db, filter_dto)
        
        total_students = int(stats_map.get("totalStudents", 0))
        fail_students = int(stats_map.get("failStudents", 0))
        
        if fail_students > total_students:
            fail_students = total_students
            
        distribution = {
            "0-59": int(stats_map.get("0-59", 0)),
            "60-69": int(stats_map.get("60-69", 0)),
            "70-79": int(stats_map.get("70-79", 0)),
            "80-89": int(stats_map.get("80-89", 0)),
            "90-100": int(stats_map.get("90-100", 0))
        }
        
        return FailRateStatisDTO(
            totalStudents=total_students,
            failStudents=fail_students,
            scoreDistribution=distribution
        )

    @staticmethod
    def get_course_names(db: Session, course_name: str) -> List[str]:
        return CourseScoreRepository.get_course_names(db, course_name)

    @staticmethod
    def get_dynamic_filter_options(db: Session, current_filter: CourseInfoFilterDTO) -> CourseInfoFilterDTO:
        terms = CourseScoreRepository.get_available_options(db, current_filter, 'c_term')
        colleges = CourseScoreRepository.get_available_options(db, current_filter, 's_college')
        majors = CourseScoreRepository.get_available_options(db, current_filter, 's_major')
        classes = CourseScoreRepository.get_available_options(db, current_filter, 's_class')
        
        return CourseInfoFilterDTO(
            courseName=current_filter.courseName,
            terms=terms,
            colleges=colleges,
            majors=majors,
            classes=classes
        )
