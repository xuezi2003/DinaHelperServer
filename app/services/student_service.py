from sqlalchemy.orm import Session
from app.services.repositories import StudentRepository
from app.models.models import Student
from app.schemas.dtos import RankDTO, SameNameDTO, MajorRankItemDTO
from app.utils.class_utils import get_major_code
from typing import Optional, List

class StudentService:
    @staticmethod
    def get_student_by_id(db: Session, student_id: str) -> Optional[Student]:
        return StudentRepository.get_by_id(db, student_id)

    @staticmethod
    def get_student_rank(db: Session, student_id: str) -> RankDTO:
        class_rank = StudentRepository.get_ranking(db, student_id, scope='class')
        major_rank = StudentRepository.get_ranking(db, student_id, scope='major')
        
        return RankDTO(
            classAvgRank=class_rank['avg_rank'],
            classGpaRank=class_rank['gpa_rank'],
            majorAvgRank=major_rank['avg_rank'],
            majorGpaRank=major_rank['gpa_rank'],
            classTotal=class_rank['total'],
            majorTotal=major_rank['total']
        )

    @staticmethod
    def get_students_by_pinyin(db: Session, pinyin: str) -> List[SameNameDTO]:
        students = StudentRepository.get_by_pinyin(db, pinyin)
        return [SameNameDTO(sId=s.studentId, sMajor=s.sMajor) for s in students]

    @staticmethod
    def get_students_by_name(db: Session, name: str) -> List[SameNameDTO]:
        students = StudentRepository.get_by_name(db, name)
        return [SameNameDTO(sId=s.studentId, sMajor=s.sMajor) for s in students]

    @staticmethod
    def get_major_ranking_list(db: Session, student: 'Student', sort_by: str = 'gpa', order: str = 'desc',
                               page: int = 1, page_size: int = 35):
        """获取学生所在专业的排名列表（分页）。
        专业由班级号前 8 位确定，返回总数、当前排名和分页数据。"""
        from app.schemas.dtos import MajorRankingResponseDTO
        
        major_code = get_major_code(student.sClass)
        if not major_code:
            return MajorRankingResponseDTO(total=0, currentRank=0, list=[])
        
        students = StudentRepository.get_major_ranking(db, major_code, sort_by, order)
        
        sort_key = (lambda s: s.sGpa or 0.0) if sort_by == 'gpa' else (lambda s: s.sAvg or 0.0)
        
        # 计算全部排名（处理并列）
        ranking_list = []
        current_rank = 0
        prev_value = None
        for idx, s in enumerate(students):
            value = sort_key(s)
            if value != prev_value:
                rank = idx + 1
                prev_value = value
            ranking_list.append(MajorRankItemDTO(
                rank=rank,
                gpa=s.sGpa or 0.0,
                avg=s.sAvg or 0.0
            ))
            if s.studentId == student.studentId:
                current_rank = rank
        
        # 分页
        total = len(ranking_list)
        start = (page - 1) * page_size
        end = start + page_size
        page_list = ranking_list[start:end]
        
        return MajorRankingResponseDTO(
            total=total,
            currentRank=current_rank,
            grade=student.sGrade or '',
            major=student.sMajor or '',
            list=page_list,
            page=page,
            pageSize=page_size,
        )
