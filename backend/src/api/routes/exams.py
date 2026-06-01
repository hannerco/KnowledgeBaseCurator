"""Endpoints para gestion y calificacion de examenes."""

import logging
import traceback

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from db.sql.database import get_db
from db.sql.models import (
    Exam,
    ExamGrade,
    ExamKey,
    ExamQuestionResult,
    ExamSubmission,
    User,
)
from db.sql.schemas import (
    ExamCreate,
    ExamGradeResponse,
    ExamKeyResponse,
    ExamKeyTextResponse,
    ExamResponse,
    ExamSubmissionDetailResponse,
    ExamSubmissionResponse,
    ExamSubmissionTextResponse,
)
from grading.engine import (
    extract_pdf_text,
    grade_submission,
    parse_exam_key,
    parse_exam_submission,
)
from utils.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Exams"], prefix="/exams")


def _get_exam_or_404(exam_id: int, db: Session, user_id: int) -> Exam:
    exam = db.query(Exam).filter(Exam.id == exam_id, Exam.user_id == user_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Examen no encontrado")
    return exam


@router.post("/", response_model=ExamResponse, summary="Crear un nuevo examen")
async def create_exam(
    payload: ExamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exam = Exam(
        user_id=current_user.id,
        title=payload.title,
        description=payload.description,
    )
    db.add(exam)
    db.commit()
    db.refresh(exam)
    return exam


@router.get("/", response_model=list[ExamResponse], summary="Listar examenes del usuario")
async def list_exams(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Exam).filter(Exam.user_id == current_user.id).all()


@router.get("/{exam_id}", response_model=ExamResponse, summary="Obtener un examen")
async def get_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _get_exam_or_404(exam_id, db, current_user.id)


@router.post(
    "/{exam_id}/key",
    response_model=ExamKeyResponse,
    summary="Subir el examen base con respuestas correctas",
)
async def upload_exam_key(
    exam_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_exam_or_404(exam_id, db, current_user.id)

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos PDF (.pdf)")

    existing_key = db.query(ExamKey).filter(ExamKey.exam_id == exam_id).first()
    if existing_key:
        raise HTTPException(status_code=409, detail="El examen ya tiene una clave registrada")

    try:
        file_bytes = await file.read()
        raw_text = extract_pdf_text(file_bytes)
        parsed_payload = parse_exam_key(raw_text)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception:
        logger.error("Error en /exams/{exam_id}/key:\n%s", traceback.format_exc())
        raise HTTPException(status_code=500, detail="Error al procesar el examen base")

    questions_count = len(parsed_payload.get("questions", []))
    db_key = ExamKey(
        exam_id=exam_id,
        filename=file.filename,
        raw_text=raw_text,
        parsed_payload=parsed_payload,
        questions_count=questions_count,
    )
    db.add(db_key)
    db.commit()
    db.refresh(db_key)
    return db_key


@router.get(
    "/{exam_id}/key/text",
    response_model=ExamKeyTextResponse,
    summary="Ver el texto extraido del examen base",
)
async def get_exam_key_text(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_exam_or_404(exam_id, db, current_user.id)
    key = db.query(ExamKey).filter(ExamKey.exam_id == exam_id).first()
    if not key:
        raise HTTPException(status_code=404, detail="Clave del examen no encontrada")
    return ExamKeyTextResponse(exam_id=exam_id, raw_text=key.raw_text)


@router.post(
    "/{exam_id}/submissions",
    response_model=ExamSubmissionResponse,
    summary="Subir un examen de estudiante",
)
async def upload_exam_submission(
    exam_id: int,
    file: UploadFile = File(...),
    student_name: str | None = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_exam_or_404(exam_id, db, current_user.id)

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos PDF (.pdf)")

    try:
        file_bytes = await file.read()
        raw_text = extract_pdf_text(file_bytes)
        parsed_payload = parse_exam_submission(raw_text)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception:
        logger.error("Error en /exams/{exam_id}/submissions:\n%s", traceback.format_exc())
        raise HTTPException(status_code=500, detail="Error al procesar el examen del estudiante")

    answers_count = len(parsed_payload.get("answers", []))
    submission = ExamSubmission(
        exam_id=exam_id,
        student_name=student_name,
        filename=file.filename,
        raw_text=raw_text,
        parsed_payload=parsed_payload,
        answers_count=answers_count,
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


@router.get(
    "/{exam_id}/submissions",
    response_model=list[ExamSubmissionResponse],
    summary="Listar submissions de un examen",
)
async def list_exam_submissions(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_exam_or_404(exam_id, db, current_user.id)
    return db.query(ExamSubmission).filter(ExamSubmission.exam_id == exam_id).all()


@router.get(
    "/{exam_id}/submissions/{submission_id}",
    response_model=ExamSubmissionDetailResponse,
    summary="Obtener detalle de una submission",
)
async def get_exam_submission(
    exam_id: int,
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_exam_or_404(exam_id, db, current_user.id)
    submission = (
        db.query(ExamSubmission)
        .filter(ExamSubmission.id == submission_id, ExamSubmission.exam_id == exam_id)
        .first()
    )
    if not submission:
        raise HTTPException(status_code=404, detail="Submission no encontrada")
    return submission


@router.get(
    "/{exam_id}/submissions/{submission_id}/text",
    response_model=ExamSubmissionTextResponse,
    summary="Ver el texto extraido de una submission",
)
async def get_exam_submission_text(
    exam_id: int,
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_exam_or_404(exam_id, db, current_user.id)
    submission = (
        db.query(ExamSubmission)
        .filter(ExamSubmission.id == submission_id, ExamSubmission.exam_id == exam_id)
        .first()
    )
    if not submission:
        raise HTTPException(status_code=404, detail="Submission no encontrada")
    return ExamSubmissionTextResponse(submission_id=submission_id, raw_text=submission.raw_text)


@router.post(
    "/{exam_id}/submissions/{submission_id}/grade",
    response_model=ExamGradeResponse,
    summary="Calificar una submission",
)
async def grade_exam_submission(
    exam_id: int,
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_exam_or_404(exam_id, db, current_user.id)

    key = db.query(ExamKey).filter(ExamKey.exam_id == exam_id).first()
    if not key:
        raise HTTPException(status_code=400, detail="No existe clave de examen registrada")

    submission = (
        db.query(ExamSubmission)
        .filter(ExamSubmission.id == submission_id, ExamSubmission.exam_id == exam_id)
        .first()
    )
    if not submission:
        raise HTTPException(status_code=404, detail="Submission no encontrada")

    if submission.grade:
        raise HTTPException(status_code=409, detail="La submission ya fue calificada")

    try:
        grading_result = grade_submission(key.parsed_payload, submission.parsed_payload)
    except Exception:
        logger.error("Error en /exams/{exam_id}/submissions/{submission_id}/grade:\n%s", traceback.format_exc())
        raise HTTPException(status_code=500, detail="Error al calificar el examen")

    grade = ExamGrade(
        submission_id=submission.id,
        total_score=grading_result["total_score"],
        max_score=grading_result["max_score"],
        percentage=grading_result["percentage"],
        confidence=grading_result["confidence"],
        needs_review=grading_result["needs_review"],
        provisional=grading_result["provisional"],
        feedback=grading_result["feedback"],
    )
    db.add(grade)
    db.flush()

    for result in grading_result["results"]:
        db.add(
            ExamQuestionResult(
                grade_id=grade.id,
                question_number=result["number"],
                question_text=result.get("question_text"),
                correct_answer=result.get("correct_answer", ""),
                student_answer=result.get("student_answer"),
                score=result["score"],
                max_score=result["max_score"],
                verdict=result["verdict"],
                confidence=result["confidence"],
                reason=result["reason"],
            )
        )

    db.commit()
    db.refresh(grade)
    return grade
