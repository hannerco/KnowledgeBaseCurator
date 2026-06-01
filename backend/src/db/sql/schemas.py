from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

class UserCreate(BaseModel):
    name: str = Field(..., min_length=1)
    email: EmailStr
    password: str = Field(..., min_length=6)

class ChatCreate(BaseModel):
    title: str = Field(..., min_length=1)
    
class ChatResponse(BaseModel):
    id: int
    user_id: int
    title: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1)
    sender: str = Field(..., pattern="^(user|system|assistant)$")
    sources: list[str] | None = None
    base_sources: list[str] | None = None
    
class MessageResponse(BaseModel):
    id: int
    chat_id: int
    content: str
    timestamp: datetime
    sender: str
    
    class Config:
        from_attributes = True

class MessagePairResponse(BaseModel):
    user_message: MessageResponse
    assistant_message: MessageResponse
    
    class Config:
        from_attributes = True
        
class DocumentResponse(BaseModel):
    id: int
    user_id: int
    filename: str
    chunks_indexed: int
    description: str | None
    document_type: str
    uploaded_at: datetime

    class Config:
        from_attributes = True


class ExamCreate(BaseModel):
    title: str = Field(..., min_length=1)
    description: str | None = None


class ExamResponse(BaseModel):
    id: int
    user_id: int
    title: str
    description: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class ExamKeyResponse(BaseModel):
    id: int
    exam_id: int
    filename: str
    questions_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class ExamKeyTextResponse(BaseModel):
    exam_id: int
    raw_text: str


class ExamSubmissionResponse(BaseModel):
    id: int
    exam_id: int
    student_name: str | None
    filename: str
    answers_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class ExamSubmissionTextResponse(BaseModel):
    submission_id: int
    raw_text: str


class ExamQuestionResultResponse(BaseModel):
    id: int
    question_number: int
    question_text: str | None
    correct_answer: str
    student_answer: str | None
    score: float
    max_score: float
    verdict: str
    confidence: float
    reason: str

    class Config:
        from_attributes = True


class ExamGradeResponse(BaseModel):
    id: int
    submission_id: int
    total_score: float
    max_score: float
    percentage: float
    confidence: float
    needs_review: bool
    provisional: bool
    feedback: str
    created_at: datetime
    question_results: list[ExamQuestionResultResponse] = []

    class Config:
        from_attributes = True


class ExamSubmissionDetailResponse(BaseModel):
    id: int
    exam_id: int
    student_name: str | None
    filename: str
    answers_count: int
    created_at: datetime
    grade: ExamGradeResponse | None

    class Config:
        from_attributes = True