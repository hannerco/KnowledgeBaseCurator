from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)
    
    chats = relationship("Chat", back_populates="user")
    documents = relationship("Document", back_populates="user")
    exams = relationship("Exam", back_populates="user")

class Chat(Base):
    __tablename__ = "chats"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="chats")
    messages = relationship(
        "Message",
        back_populates="chat",
        cascade="all, delete-orphan"
    )
    
class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    content = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    sender = Column(String, nullable=False)
    
    chat = relationship("Chat", back_populates="messages")

    
class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String, nullable=False)
    chunks_indexed = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    document_type = Column(String, default="user_upload", server_default="user_upload")
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="documents")


class Exam(Base):
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="exams")
    key = relationship("ExamKey", back_populates="exam", uselist=False, cascade="all, delete-orphan")
    submissions = relationship("ExamSubmission", back_populates="exam", cascade="all, delete-orphan")


class ExamKey(Base):
    __tablename__ = "exam_keys"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id", ondelete="CASCADE"), nullable=False, unique=True)
    filename = Column(String, nullable=False)
    raw_text = Column(Text, nullable=False)
    parsed_payload = Column(JSON, nullable=False)
    questions_count = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    exam = relationship("Exam", back_populates="key")


class ExamSubmission(Base):
    __tablename__ = "exam_submissions"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id", ondelete="CASCADE"), nullable=False)
    student_name = Column(String, nullable=True)
    filename = Column(String, nullable=False)
    raw_text = Column(Text, nullable=False)
    parsed_payload = Column(JSON, nullable=False)
    answers_count = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    exam = relationship("Exam", back_populates="submissions")
    grade = relationship("ExamGrade", back_populates="submission", uselist=False, cascade="all, delete-orphan")


class ExamGrade(Base):
    __tablename__ = "exam_grades"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("exam_submissions.id", ondelete="CASCADE"), nullable=False, unique=True)
    total_score = Column(Float, nullable=False)
    max_score = Column(Float, nullable=False)
    percentage = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    needs_review = Column(Boolean, default=False)
    provisional = Column(Boolean, default=False)
    feedback = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    submission = relationship("ExamSubmission", back_populates="grade")
    question_results = relationship("ExamQuestionResult", back_populates="grade", cascade="all, delete-orphan")


class ExamQuestionResult(Base):
    __tablename__ = "exam_question_results"

    id = Column(Integer, primary_key=True, index=True)
    grade_id = Column(Integer, ForeignKey("exam_grades.id", ondelete="CASCADE"), nullable=False)
    question_number = Column(Integer, nullable=False)
    question_text = Column(Text, nullable=True)
    correct_answer = Column(Text, nullable=False)
    student_answer = Column(Text, nullable=True)
    score = Column(Float, nullable=False)
    max_score = Column(Float, nullable=False)
    verdict = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    reason = Column(Text, nullable=False)

    grade = relationship("ExamGrade", back_populates="question_results")
    
    