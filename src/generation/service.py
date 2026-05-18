import json

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


def _validate_question(raw: GeneratedQuestion, expected_type: QuestionType) -> None:
    if raw.type != expected_type:
        raise GenerationError(
            f"Ожидался тип {expected_type.value}, получен {raw.type.value}"
        )

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


def _to_generated(raw: _LLMQuestionsBatch, req: GenerateQuestionsRequest) -> list[GeneratedQuestion]:
    if len(raw.questions) != req.count:
        raise GenerationError(
            f"Ожидалось {req.count} вопросов, модель вернула {len(raw.questions)}"
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
        _validate_question(question, req.question_type)
        result.append(question)
    return result


def generate_questions(req: GenerateQuestionsRequest) -> GenerateQuestionsResponse:
    settings = get_settings()
    if req.count > settings.max_questions_per_request:
        raise GenerationError(
            f"count не может превышать {settings.max_questions_per_request}"
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
    )
