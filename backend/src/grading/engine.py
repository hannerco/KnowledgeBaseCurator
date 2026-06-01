"""AI-first grading engine for exams.

This module extracts text from PDFs, parses questions and answers using an LLM,
then grades student submissions using the exam key as the only source of truth.
"""

from __future__ import annotations

import io
import json
from typing import Any

from pypdf import PdfReader
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

from config import settings


def extract_pdf_text(file_bytes: bytes) -> str:
    """Extract text from a digital PDF. Raises ValueError if empty."""
    reader = PdfReader(io.BytesIO(file_bytes))
    pages: list[str] = []

    for page in reader.pages:
        text = page.extract_text() or ""
        text = text.strip()
        if text:
            pages.append(text)

    full_text = "\n\n".join(pages).strip()
    full_text = _normalize_extracted_text(full_text)
    if not full_text:
        raise ValueError("El PDF no contiene texto extraible.")

    return full_text


def parse_exam_key(raw_text: str) -> dict:
    """Parse the exam key (correct answers) into structured JSON."""
    prompt = _build_key_prompt(raw_text)
    payload = _call_llm_json(prompt)

    questions = _validate_key_questions(payload.get("questions"))
    if not questions:
        raise ValueError("No se detectaron preguntas con numeracion obligatoria.")

    return {"questions": questions}


def parse_exam_submission(raw_text: str) -> dict:
    """Parse a student submission into structured JSON."""
    prompt = _build_submission_prompt(raw_text)
    payload = _call_llm_json(prompt)

    answers = _validate_submission_answers(payload.get("answers"))
    if not answers:
        raise ValueError("No se detectaron respuestas con numeracion obligatoria.")

    return {"answers": answers}


def grade_submission(parsed_key: dict, parsed_submission: dict) -> dict:
    """Grade the submission using the parsed key and LLM scoring."""
    key_questions = parsed_key.get("questions", [])
    answers = parsed_submission.get("answers", [])
    answer_map = {item["number"]: item["answer"] for item in answers}

    items = []
    for q in key_questions:
        items.append(
            {
                "number": q["number"],
                "question_text": q.get("question_text", ""),
                "correct_answer": q.get("correct_answer", ""),
                "student_answer": answer_map.get(q["number"], ""),
            }
        )

    grading_prompt = _build_grading_prompt(items)
    grading_payload = _call_llm_json(grading_prompt)
    results = _coerce_grading_results(grading_payload.get("results"), items)

    max_score = sum(result["max_score"] for result in results)
    total_score = sum(result["score"] for result in results)
    percentage = (total_score / max_score * 100.0) if max_score else 0.0

    if results:
        confidence = sum(result["confidence"] for result in results) / len(results)
    else:
        confidence = 0.0

    needs_review = any(
        result["confidence"] < settings.GRADING_CONFIDENCE_THRESHOLD
        for result in results
    )

    feedback = generate_feedback(
        results=results,
        total_score=total_score,
        max_score=max_score,
        percentage=percentage,
    )

    return {
        "results": results,
        "total_score": total_score,
        "max_score": max_score,
        "percentage": percentage,
        "confidence": confidence,
        "needs_review": needs_review,
        "provisional": needs_review,
        "feedback": feedback,
    }


def generate_feedback(
    *,
    results: list[dict],
    total_score: float,
    max_score: float,
    percentage: float,
) -> str:
    """Generate general feedback for the exam based on grading results."""
    summary = {
        "total_score": total_score,
        "max_score": max_score,
        "percentage": round(percentage, 2),
        "results": [
            {
                "number": r["number"],
                "verdict": r["verdict"],
                "reason": r["reason"],
            }
            for r in results
        ],
    }

    prompt = f"""
Eres un asistente academico. Debes generar un feedback general del examen.

Reglas estrictas:
- Usa solo la informacion entregada en JSON.
- No inventes datos ni menciones preguntas especificas con texto completo.
- No hagas listas ni markdown. Solo parrafos cortos.
- Escribe entre 3 y 6 oraciones.

JSON:
{json.dumps(summary, ensure_ascii=False)}

Respuesta:
"""

    llm = ChatGroq(
        model=settings.GROQ_MODEL,
        api_key=settings.GROQ_API_KEY,
        temperature=0,
    )

    response = llm.invoke([HumanMessage(content=prompt)])
    return (response.content or "").strip()


def _call_llm_json(prompt: str) -> dict:
    llm = ChatGroq(
        model=settings.GROQ_MODEL,
        api_key=settings.GROQ_API_KEY,
        temperature=0,
    )
    response = llm.invoke([HumanMessage(content=prompt)])
    raw = (response.content or "").strip()
    json_text = _extract_json_block(raw)
    try:
        return json.loads(json_text)
    except json.JSONDecodeError:
        sanitized = _escape_control_chars_in_json(json_text)
        try:
            return json.loads(sanitized)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "No se pudo interpretar la respuesta del modelo. "
                "Verifica que el PDF tenga texto limpio y numeracion 1), 2), 3)."
            ) from exc


def _extract_json_block(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        cleaned = "\n".join(lines[1:-1]).strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("No se encontro JSON valido en la respuesta del modelo.")

    return cleaned[start : end + 1]


def _normalize_extracted_text(text: str) -> str:
    """Normalize extracted PDF text by removing problematic control chars."""
    normalized = text.replace("\x0c", "\n")
    return "".join(
        ch
        for ch in normalized
        if ch in ("\n", "\t") or ord(ch) >= 32
    ).strip()


def _escape_control_chars_in_json(text: str) -> str:
    """Escape control characters inside JSON strings to improve parsing."""
    result: list[str] = []
    in_string = False
    escaped = False

    for ch in text:
        if in_string:
            if escaped:
                result.append(ch)
                escaped = False
                continue

            if ch == "\\":
                result.append(ch)
                escaped = True
                continue

            if ch == '"':
                in_string = False
                result.append(ch)
                continue

            if ch == "\n":
                result.append("\\n")
                continue
            if ch == "\r":
                result.append("\\r")
                continue
            if ch == "\t":
                result.append("\\t")
                continue

            code = ord(ch)
            if code < 32:
                result.append(f"\\u{code:04x}")
                continue

            result.append(ch)
            continue

        if ch == '"':
            in_string = True
        result.append(ch)

    return "".join(result)


def _validate_key_questions(items: Any) -> list[dict]:
    questions: list[dict] = []
    seen = set()

    if not isinstance(items, list):
        return questions

    for item in items:
        if not isinstance(item, dict):
            continue

        try:
            number = int(item.get("number"))
        except (TypeError, ValueError):
            continue

        if number in seen:
            continue

        question_text = str(item.get("question_text") or "").strip()
        correct_answer = str(item.get("correct_answer") or "").strip()
        if not correct_answer:
            continue

        questions.append(
            {
                "number": number,
                "question_text": question_text,
                "correct_answer": correct_answer,
            }
        )
        seen.add(number)

    questions.sort(key=lambda q: q["number"])
    return questions


def _validate_submission_answers(items: Any) -> list[dict]:
    answers: list[dict] = []
    seen = set()

    if not isinstance(items, list):
        return answers

    for item in items:
        if not isinstance(item, dict):
            continue

        try:
            number = int(item.get("number"))
        except (TypeError, ValueError):
            continue

        if number in seen:
            continue

        answer = str(item.get("answer") or "").strip()
        if not answer:
            continue

        answers.append({"number": number, "answer": answer})
        seen.add(number)

    answers.sort(key=lambda a: a["number"])
    return answers


def _coerce_grading_results(raw_results: Any, items: list[dict]) -> list[dict]:
    results_map: dict[int, dict] = {}

    if isinstance(raw_results, list):
        for item in raw_results:
            if not isinstance(item, dict):
                continue
            try:
                number = int(item.get("number"))
            except (TypeError, ValueError):
                continue

            results_map[number] = item

    results: list[dict] = []

    for item in items:
        number = item["number"]
        candidate = results_map.get(number, {})

        score = _safe_float(candidate.get("score"), default=0.0)
        max_score = _safe_float(candidate.get("max_score"), default=1.0)
        if max_score <= 0:
            max_score = 1.0

        if score < 0:
            score = 0.0
        if score > max_score:
            score = max_score

        confidence = _safe_float(candidate.get("confidence"), default=0.0)
        if confidence < 0:
            confidence = 0.0
        if confidence > 1:
            confidence = 1.0

        verdict = str(candidate.get("verdict") or "").strip().lower()
        if not verdict:
            verdict = "unanswered" if not item["student_answer"] else "incorrect"

        reason = str(candidate.get("reason") or "").strip()
        if not reason:
            reason = "Sin razon detallada." if item["student_answer"] else "Sin respuesta del estudiante."

        results.append(
            {
                "number": number,
                "question_text": item.get("question_text", ""),
                "correct_answer": item.get("correct_answer", ""),
                "student_answer": item.get("student_answer", ""),
                "score": score,
                "max_score": max_score,
                "verdict": verdict,
                "confidence": confidence,
                "reason": reason,
            }
        )

    return results


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _build_key_prompt(raw_text: str) -> str:
    return f"""
Eres un parser estricto de examenes resueltos.

Debes extraer preguntas y respuestas correctas del texto base.
Reglas:
- Usa solo el texto dado. No inventes preguntas.
- La numeracion obligatoria es: 1) 2) 3) ...
- Si una respuesta tiene varias lineas, conserva los saltos de linea con \n.
- Devuelve SOLO JSON valido, sin markdown.

Formato JSON exacto:
{{
  "questions": [
    {{
      "number": 1,
      "question_text": "Texto de la pregunta",
      "correct_answer": "Respuesta correcta"
    }}
  ]
}}

Texto:
{raw_text}

JSON:
"""


def _build_submission_prompt(raw_text: str) -> str:
    return f"""
Eres un parser estricto de examenes de estudiantes.

Debes extraer solo las respuestas del estudiante usando la numeracion obligatoria.
Reglas:
- Usa solo el texto dado. No inventes respuestas.
- La numeracion obligatoria es: 1) 2) 3) ...
- Si una respuesta tiene varias lineas, conserva los saltos de linea con \n.
- Devuelve SOLO JSON valido, sin markdown.

Formato JSON exacto:
{{
  "answers": [
    {{
      "number": 1,
      "answer": "Respuesta del estudiante"
    }}
  ]
}}

Texto:
{raw_text}

JSON:
"""


def _build_grading_prompt(items: list[dict]) -> str:
    return f"""
Eres un calificador academico justo y consistente.

Debes comparar cada respuesta del estudiante con la respuesta correcta.
Reglas:
- Usa solo la respuesta correcta como fuente de verdad.
- No uses conocimiento externo.
- Considera el texto de la pregunta para entender el nivel de detalle esperado.
- Para preguntas abiertas, acepta como correcto si el estudiante expresa la idea principal aunque no incluya detalles adicionales.
- Solo exige detalles especificos cuando la pregunta los pide de forma explicita (numero, lista, fecha, definicion completa).
- Para verdadero/falso o seleccion multiple, aplica criterio estricto.
- Califica con max_score = 1.0 por pregunta.
- score puede ser 0, 0.5 o 1.0 segun exactitud.
- verdict debe ser: correct, incorrect, partial, unanswered.
- confidence debe estar entre 0.0 y 1.0.
- Devuelve SOLO JSON valido, sin markdown.

Formato JSON exacto:
{{
  "results": [
    {{
      "number": 1,
      "score": 1.0,
      "max_score": 1.0,
      "verdict": "correct",
      "confidence": 0.92,
      "reason": "Explicacion breve."
    }}
  ]
}}

Datos:
{json.dumps({"items": items}, ensure_ascii=False)}

JSON:
"""
