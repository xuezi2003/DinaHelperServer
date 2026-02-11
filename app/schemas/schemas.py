from pydantic import BaseModel, ConfigDict
from typing import List, Optional

class CourseScoreBase(BaseModel):
    studentId: str
    courseName: str
    score: Optional[float] = None
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
