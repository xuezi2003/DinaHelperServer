from pydantic import BaseModel, ConfigDict
from typing import List, Optional

class StudentBase(BaseModel):
    studentId: str
    sName: str
    sPy: Optional[str] = None
    sCollege: Optional[str] = None
    sMajor: Optional[str] = None
    sGrade: Optional[str] = None
    sClass: Optional[str] = None
    sAvg: Optional[float] = None
    sGpa: Optional[float] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class CourseScoreBase(BaseModel):
    studentId: str
    courseName: str
    score: float
    cTerm: str
    cType: Optional[str] = None
    cHours: Optional[str] = None
    cCredit: float
    cPass: int

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class ScoreQueryDTO(BaseModel):
    avg: Optional[float] = None
    gpa: Optional[float] = None
    dataList: List[CourseScoreBase] = []

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
