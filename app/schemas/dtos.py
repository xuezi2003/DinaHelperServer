from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict

class CourseInfoFilterDTO(BaseModel):
    courseName: Optional[str] = None
    terms: List[str] = []
    colleges: List[str] = []
    majors: List[str] = []
    classes: List[str] = []
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class FailRateStatisDTO(BaseModel):
    totalStudents: int = 0
    failStudents: int = 0
    scoreDistribution: Dict[str, int] = {}
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class RankDTO(BaseModel):
    classAvgRank: int
    classGpaRank: int
    majorAvgRank: int
    majorGpaRank: int
    classTotal: int
    majorTotal: int

class SameNameDTO(BaseModel):
    sId: str
    sMajor: str

class MajorRankItemDTO(BaseModel):
    rank: int
    gpa: float
    avg: float

class MajorRankingResponseDTO(BaseModel):
    total: int
    currentRank: int
    grade: str = ''
    major: str = ''
    list: List[MajorRankItemDTO] = []

class ChallengeResponseDTO(BaseModel):
    token: str
    questions: List[str] = []

class VerifyAnswerItem(BaseModel):
    courseName: str
    score: float

class VerifiedQueryDTO(BaseModel):
    sid: str
    token: str = ''
    answers: List[VerifyAnswerItem] = []
    sessionToken: str = ''
    wxToken: str = ''
