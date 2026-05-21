from src.generation.schemas import Difficulty, GenerateQuestionsRequest, QuestionType

_DIFFICULTY_LABELS = {
    Difficulty.EASY: "лёгкий",
    Difficulty.MEDIUM: "средний",
    Difficulty.HARD: "сложный",
}

_TYPE_LABELS = {
    QuestionType.SINGLE_CHOICE: "один правильный вариант (single_choice)",
    QuestionType.MULTIPLE_CHOICE: "несколько правильных вариантов (multiple_choice)",
    QuestionType.TEXT: "текстовый ответ без вариантов (text)",
}


def _rules_for_type(q_type: QuestionType) -> list[str]:
    label = _TYPE_LABELS[q_type]
    rules = [f"Тип: {q_type.value} — {label}."]
    if q_type in (QuestionType.SINGLE_CHOICE, QuestionType.MULTIPLE_CHOICE):
        rules.append("У каждого такого вопроса 4 варианта (options) с полями text и is_correct.")
        if q_type == QuestionType.SINGLE_CHOICE:
            rules.append("Ровно один вариант с is_correct=true.")
        else:
            rules.append("Минимум два варианта с is_correct=true.")
    else:
        rules.append("Поле options — пустой массив; укажи correct_text с эталонным ответом.")
    return rules


def build_generation_messages(req: GenerateQuestionsRequest) -> list[dict[str, str]]:
    assert req.questions is not None

    difficulty = (
        _DIFFICULTY_LABELS[req.difficulty]
        if req.difficulty
        else "средний"
    )

    system = (
        "Ты — эксперт по составлению проверочных вопросов для образовательной платформы. "
        "Генерируй только достоверные вопросы по заданной теме. "
        "Отвечай строго в формате JSON по схеме: список questions. "
        "У каждого элемента questions поле type должно соответствовать заданному типу. "
        "Язык вопросов и вариантов — тот, что указан в запросе."
    )

    distribution_lines = [
        f"- {spec.count} вопрос(ов) типа {spec.type.value} ({_TYPE_LABELS[spec.type]})"
        for spec in req.questions
    ]

    rules = [
        f"Всего вопросов в ответе: ровно {req.total_count}.",
        "Распределение по типам:",
        *distribution_lines,
        f"Баллы за каждый вопрос: {req.points}.",
        f"Сложность: {difficulty}.",
        "Добавь краткое explanation и hint к каждому вопросу.",
    ]

    for spec in req.questions:
        rules.append(f"\nПравила для типа {spec.type.value} ({spec.count} шт.):")
        rules.extend(f"  {line}" for line in _rules_for_type(spec.type))

    user_parts = [
        f"Тема: {req.topic}",
        f"Язык: {req.language}",
        "Правила:\n" + "\n".join(rules),
    ]
    if req.context:
        user_parts.append(f"Контекст для опоры на материалы:\n{req.context}")

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": "\n\n".join(user_parts)},
    ]
