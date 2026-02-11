from pydantic import BaseModel, ConfigDict, Field
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
    page: int = 1
    pageSize: int = 35

class RecFilterDTO(BaseModel):
    year: int
    college: Optional[str] = None
    major: Optional[str] = None
    page: int = 1
    pageSize: int = 35

class RecOptionsDTO(BaseModel):
    years: List[int] = []
    colleges: List[str] = []
    majors: List[str] = []

class RecItemDTO(BaseModel):
    college: Optional[str] = None
    major: Optional[str] = None
    recGpa: Optional[float] = None
    latestGpa: Optional[float] = None
    perfScore: Optional[float] = None
    compScore: Optional[float] = None
    compRank: Optional[int] = None
    latestGpaRank: Optional[int] = None
    remark: str = ''

class RecSummaryDTO(BaseModel):
    recommended: int = 0
    majorTotal: Optional[int] = None
    rate: Optional[str] = None

class RecListResponseDTO(BaseModel):
    summary: RecSummaryDTO
    list: List[RecItemDTO] = []
    total: int = 0
    page: int = 1
    pageSize: int = 35


class ChallengeResponseDTO(BaseModel):
    token: str
    questions: List[str] = []

class VerifyAnswerItem(BaseModel):
    courseName: str
    score: float

class VerifiedQueryDTO(BaseModel):
    sid: str = Field(..., max_length=20)
    token: str = ''
    answers: List[VerifyAnswerItem] = []
    sessionToken: str = ''
