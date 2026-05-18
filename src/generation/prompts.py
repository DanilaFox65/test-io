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


def build_generation_messages(req: GenerateQuestionsRequest) -> list[dict[str, str]]:
    difficulty = (
        _DIFFICULTY_LABELS[req.difficulty]
        if req.difficulty
        else "средний"
    )
    type_label = _TYPE_LABELS[req.question_type]

    system = (
        "Ты — эксперт по составлению проверочных вопросов для образовательной платформы. "
        "Генерируй только достоверные вопросы по заданной теме. "
        "Отвечай строго в формате JSON по схеме: список questions. "
        "Язык вопросов и вариантов — тот, что указан в запросе."
    )

    rules = [
        f"Количество вопросов: ровно {req.count}.",
        f"Тип каждого вопроса: {req.question_type.value} ({type_label}).",
        f"Баллы за каждый вопрос: {req.points}.",
        f"Сложность: {difficulty}.",
    ]

    if req.question_type in (QuestionType.SINGLE_CHOICE, QuestionType.MULTIPLE_CHOICE):
        rules.append("У каждого вопроса 4 варианта ответа (options), у каждого поле text и is_correct.")
        if req.question_type == QuestionType.SINGLE_CHOICE:
            rules.append("Ровно один вариант с is_correct=true.")
        else:
            rules.append("Минимум два варианта с is_correct=true.")
    else:
        rules.append("Поле options — пустой массив; укажи correct_text с эталонным ответом.")

    rules.append("Добавь краткое explanation (почему ответ верный) и hint (подсказка без прямого ответа).")

    user_parts = [
        f"Тема: {req.topic}",
        f"Язык: {req.language}",
        "Правила:\n- " + "\n- ".join(rules),
    ]
    if req.context:
        user_parts.append(f"Контекст для опоры на материалы:\n{req.context}")

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": "\n\n".join(user_parts)},
    ]
