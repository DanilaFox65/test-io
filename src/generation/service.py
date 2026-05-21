import json
from collections import Counter

from mistralai.extra.utils.response_format import response_format_from_pydantic_model

from core.mistral_client import get_mistral_client
from core.settings import get_settings
from src.generation.prompts import build_generation_messages
from src.generation.schemas import (
    GenerateQuestionsRequest,
    GenerateQuestionsResponse,
    GeneratedOption,
    GeneratedQuestion,
    QuestionType,
    _LLMQuestionsBatch,
)


class GenerationError(Exception):
    pass


def _expected_type_counts(req: GenerateQuestionsRequest) -> Counter[QuestionType]:
    assert req.questions is not None
    counts: Counter[QuestionType] = Counter()
    for spec in req.questions:
        counts[spec.type] += spec.count
    return counts


def _validate_question(raw: GeneratedQuestion) -> None:
    if raw.type in (QuestionType.SINGLE_CHOICE, QuestionType.MULTIPLE_CHOICE):
        if len(raw.options) < 2:
            raise GenerationError("У вопроса с вариантами должно быть минимум 2 option")
        for opt in raw.options:
            if not opt.text.strip():
                raise GenerationError("Пустой текст варианта ответа")
        correct = [o for o in raw.options if o.is_correct]
        if raw.type == QuestionType.SINGLE_CHOICE and len(correct) != 1:
            raise GenerationError(
                "single_choice: ровно один вариант должен быть is_correct=true"
            )
        if raw.type == QuestionType.MULTIPLE_CHOICE and len(correct) < 2:
            raise GenerationError(
                "multiple_choice: минимум два варианта с is_correct=true"
            )
    elif raw.type == QuestionType.TEXT:
        if raw.options:
            raise GenerationError("text: options должен быть пустым")
        if not raw.correct_text or not raw.correct_text.strip():
            raise GenerationError("text: требуется correct_text")


def _to_generated(
    raw: _LLMQuestionsBatch, req: GenerateQuestionsRequest
) -> list[GeneratedQuestion]:
    expected_total = req.total_count
    if len(raw.questions) != expected_total:
        raise GenerationError(
            f"Ожидалось {expected_total} вопросов, модель вернула {len(raw.questions)}"
        )

    result: list[GeneratedQuestion] = []
    for item in raw.questions:
        question = GeneratedQuestion(
            text=item.text.strip(),
            type=QuestionType(item.type),
            points=item.points,
            options=[
                GeneratedOption(text=o.text.strip(), is_correct=o.is_correct)
                for o in item.options
            ],
            correct_text=item.correct_text.strip() if item.correct_text else None,
            explanation=item.explanation.strip() if item.explanation else None,
            hint=item.hint.strip() if item.hint else None,
        )
        if not question.text:
            raise GenerationError("Пустой текст вопроса")
        _validate_question(question)
        result.append(question)

    actual_counts = Counter(q.type for q in result)
    expected_counts = _expected_type_counts(req)
    if actual_counts != expected_counts:
        raise GenerationError(
            "Неверное распределение типов: "
            f"ожидалось {dict((k.value, v) for k, v in expected_counts.items())}, "
            f"получено {dict((k.value, v) for k, v in actual_counts.items())}"
        )

    return result


def generate_questions(req: GenerateQuestionsRequest) -> GenerateQuestionsResponse:
    settings = get_settings()
    # Лимит также проверяется в GenerateQuestionsRequest.check_count_limits (422).
    if req.total_count > settings.max_questions_per_request:
        raise GenerationError(
            f"Сумма count ({req.total_count}) превышает MAX_QUESTIONS_PER_REQUEST="
            f"{settings.max_questions_per_request}"
        )

    client = get_mistral_client()
    messages = build_generation_messages(req)
    response_format = response_format_from_pydantic_model(_LLMQuestionsBatch)

    try:
        response = client.chat.complete(
            model=settings.mistral_model,
            messages=messages,
            response_format=response_format,
            temperature=0.4,
        )
    except Exception as exc:
        raise GenerationError(f"Mistral API: {exc}") from exc

    content = response.choices[0].message.content
    if not content:
        raise GenerationError("Пустой ответ от Mistral")

    try:
        payload = json.loads(content)
        batch = _LLMQuestionsBatch.model_validate(payload)
    except (json.JSONDecodeError, ValueError) as exc:
        raise GenerationError(f"Не удалось разобрать JSON от модели: {exc}") from exc

    questions = _to_generated(batch, req)
    return GenerateQuestionsResponse(
        questions=questions,
        model=settings.mistral_model,
        topic=req.topic,
        total_count=req.total_count,
    )
