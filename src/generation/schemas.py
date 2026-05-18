from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class QuestionType(str, Enum):
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    TEXT = "text"


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class GenerateQuestionsRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=500)
    question_type: QuestionType = QuestionType.SINGLE_CHOICE
    count: int = Field(default=3, ge=1, le=10)
    difficulty: Difficulty | None = None
    language: str = Field(default="ru", min_length=2, max_length=10)
    points: int = Field(default=10, ge=1, le=100)
    context: str | None = Field(
        default=None,
        max_length=4000,
        description="Дополнительный контекст (материалы урока, описание квеста)",
    )


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
