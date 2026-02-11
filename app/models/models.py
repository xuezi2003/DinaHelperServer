from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from sqlalchemy.sql import func
from app.db.session import Base

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

class Recommendation(Base):
    __tablename__ = "recommendation"

    studentId = Column("s_id", String(14), primary_key=True)
    year = Column("year", Integer, primary_key=True)
    name = Column("name", String(20))
    gender = Column("gender", String(2))
    political = Column("political", String(20))
    college = Column("college", String(60))
    major = Column("major", String(60))
    courseGpa = Column("course_gpa", Float)
    courseAvg = Column("course_avg", Float, nullable=True)
    perfScore = Column("perf_score", Float, nullable=True)
    compScore = Column("comp_score", Float)
    compRank = Column("comp_rank", Integer)
    majorTotal = Column("major_total", Integer, nullable=True)
    remark = Column("remark", String(100))


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


class Notice(Base):
    __tablename__ = "notice"

    key = Column("notice_key", String(50), primary_key=True)
    content = Column("content", Text, nullable=False, default="")
    updatedAt = Column("updated_at", DateTime, server_default=func.now(), onupdate=func.now())
