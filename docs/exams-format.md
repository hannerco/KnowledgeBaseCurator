# Exam PDF format guide (base key and student submission)

This guide defines the exact format to generate PDF files that the grading system can parse reliably.
All PDFs must be digital text (not scanned images).

## Global requirements

- The numbering is mandatory and must be exactly: `1)`, `2)`, `3)`, ...
- One question per number.
- Use blank lines between questions.
- Multi-line answers are allowed. Keep them directly under the number.
- Avoid extra numbered lists inside answers (use `-` or `*` instead).
- Use ASCII if possible. Accents are OK, but keep consistent formatting.
- Do not embed images as the only source of answers.

## Base exam (answer key) format

The base exam must contain each question and its correct answer.
Recommended structure:

```
1) Pregunta: Que es la fotosintesis?
Respuesta: Proceso por el cual las plantas convierten luz en energia quimica.

2) Pregunta: Verdadero o falso: La celula es la unidad basica de la vida.
Respuesta: Verdadero.

3) Pregunta: Complete: La ley de Ohm dice que V = ____
Respuesta: I * R.

4) Pregunta: Explica en dos lineas la diferencia entre mitosis y meiosis.
Respuesta: La mitosis produce celulas identicas para crecimiento.
La meiosis produce gametos con mitad de cromosomas.
```

Notes:
- The line `Pregunta:` is optional but recommended.
- The line `Respuesta:` is optional but recommended.
- Multi-line answers should continue on the next line without a new number.

## Student exam (gradable submission) format

The student submission must contain only answers with the same numbering.
Recommended structure:

```
1) Respuesta: Proceso donde las plantas usan luz para producir energia.

2) Respuesta: Verdadero.

3) Respuesta: I * R

4) Respuesta: La mitosis genera celulas iguales para crecer.
La meiosis genera gametos con la mitad del material genetico.
```

Notes:
- The line `Respuesta:` is optional but recommended.
- The numbering must match the base exam.
- Extra text before the first number should be avoided.

## Common pitfalls to avoid

- Missing the `)` after the number (example: `1.` or `1-`).
- Multiple answers under the same number.
- Extra numbered lists inside an answer.
- Mixed numbering styles in the same document.
- Scanned PDFs or images without real text.

## Quick checklist

- [ ] PDF is digital text
- [ ] Uses `1)`, `2)`, `3)` consistently
- [ ] One question per number
- [ ] Answers are right below the number
- [ ] No extra numbering inside answers
