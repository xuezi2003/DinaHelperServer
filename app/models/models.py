from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from app.db.session import Base
from datetime import datetime

class Student(Base):
    __tablename__ = "student"

    studentId = Column("s_id", String(14), primary_key=True, index=True)
    sName = Column("s_name", String(50))
    sPy = Column("s_py", String(100))
    sCollege = Column("s_college", String(100))
    sMajor = Column("s_major", String(100))
    sGrade = Column("s_grade", String(20))
    sClass = Column("s_class", String(50))
    sAvg = Column("s_avg", Float)
    sGpa = Column("s_gpa", Float)
    classAvgRank = Column("class_avg_rank", Integer)
    classGpaRank = Column("class_gpa_rank", Integer)
    majorAvgRank = Column("major_avg_rank", Integer)
    majorGpaRank = Column("major_gpa_rank", Integer)

class CourseScore(Base):
    __tablename__ = "course_score"

    studentId = Column("s_id", String(14), primary_key=True, index=True)
    cTerm = Column("c_term", String(8), primary_key=True)
    courseName = Column("c_name", String(100), primary_key=True)
    
    score = Column("c_score", Float)
    cType = Column("c_type", String(50))
    cHours = Column("c_hours", String(20))
    cCredit = Column("c_credit", Float)
    cPass = Column("c_pass", Integer)  # 0-正常 1-补考 2-重修 3-刷分


class UserFeedback(Base):
    __tablename__ = "user_feedback"
    id = Column("id", Integer, primary_key=True, autoincrement=True)
    studentId = Column("s_id", String(50))
    content = Column("content", String(255))
    createTime = Column("create_time", DateTime, default=datetime.now)

