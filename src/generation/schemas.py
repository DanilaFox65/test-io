from collections import Counter
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from core.settings import get_settings


class QuestionType(str, Enum):
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    TEXT = "text"


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class QuestionTypeSpec(BaseModel):
    type: QuestionType
    count: int = Field(ge=1)


class GenerateQuestionsRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=500)
    questions: list[QuestionTypeSpec] | None = Field(
        default=None,
        min_length=1,
        description="Список типов и количества (новый формат)",
    )
    question_type: QuestionType | None = Field(
        default=None,
        description="Устаревший формат: один тип на весь запрос",
    )
    count: int | None = Field(
        default=None,
        ge=1,
        description="Устаревший формат: количество при одном question_type",
    )
    difficulty: Difficulty | None = None
    language: str = Field(default="ru", min_length=2, max_length=10)
    points: int = Field(default=10, ge=1, le=100)
    context: str | None = Field(
        default=None,
        max_length=4000,
        description="Дополнительный контекст (материалы урока, описание квеста)",
    )

    @model_validator(mode="after")
    def normalize_questions(self) -> "GenerateQuestionsRequest":
        if not self.questions:
            q_type = self.question_type or QuestionType.SINGLE_CHOICE
            q_count = self.count if self.count is not None else 3
            self.questions = [QuestionTypeSpec(type=q_type, count=q_count)]
            return self

        merged: Counter[QuestionType] = Counter()
        for spec in self.questions:
            merged[spec.type] += spec.count
        self.questions = [
            QuestionTypeSpec(type=q_type, count=q_count)
            for q_type, q_count in merged.items()
        ]
        return self

    @model_validator(mode="after")
    def check_count_limits(self) -> "GenerateQuestionsRequest":
        max_allowed = get_settings().max_questions_per_request
        for spec in self.questions or []:
            if spec.count > max_allowed:
                raise ValueError(
                    f"count для типа {spec.type.value} не может превышать "
                    f"{max_allowed} (MAX_QUESTIONS_PER_REQUEST)"
                )
        if self.total_count > max_allowed:
            raise ValueError(
                f"Сумма count ({self.total_count}) превышает лимит {max_allowed} "
                f"(MAX_QUESTIONS_PER_REQUEST)"
            )
        return self

    @property
    def total_count(self) -> int:
        return sum(spec.count for spec in self.questions or [])


class GeneratedOption(BaseModel):
    text: str
    is_correct: bool


class GeneratedQuestion(BaseModel):
    text: str
    type: QuestionType
    points: int
    options: list[GeneratedOption] = Field(default_factory=list)
    correct_text: str | None = None
    explanation: str | None = None
    hint: str | None = None


class GenerateQuestionsResponse(BaseModel):
    questions: list[GeneratedQuestion]
    model: str
    topic: str
    total_count: int


# --- схема ответа Mistral (structured output) ---


class _LLMOption(BaseModel):
    text: str
    is_correct: bool


class _LLMQuestion(BaseModel):
    text: str
    type: Literal["single_choice", "multiple_choice", "text"]
    points: int
    options: list[_LLMOption] = Field(default_factory=list)
    correct_text: str | None = None
    explanation: str | None = None
    hint: str | None = None


class _LLMQuestionsBatch(BaseModel):
    questions: list[_LLMQuestion]

    @field_validator("questions")
    @classmethod
    def not_empty(cls, value: list[_LLMQuestion]) -> list[_LLMQuestion]:
        if not value:
            raise ValueError("questions must not be empty")
        return value
