# Установка и запуск

1. Создание .env файла (можно взять из примера)
2. Запуск docker-compose файла (docker-compose up)
3. Прогнать миграции в БД (alembic upgrade head)
4. Пользуйтесь

## OpenAI integration

1. Add API key to `.env`

```env
OPENAI_API_KEY=sk-...
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Endpoint

POST `/assistant`

Body:

```json
{
  "message": "Hello"
}
```
