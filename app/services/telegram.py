import httpx
from app.core.config import settings
from app.services.rag import answer_question


async def handle_telegram_update(update: dict) -> None:
    message = update.get("message") or update.get("edited_message")
    if not message or not message.get("text"):
        return
    chat_id = str(message.get("chat", {}).get("id", ""))
    if not chat_id or chat_id not in settings.telegram_chat_allowlist:
        return
    question = message["text"].strip()
    if question.startswith("/start"):
        answer = "RAG assistant ready. Send a question to search your connected knowledge base."
    else:
        if question.startswith("/ask"):
            question = question[4:].strip()
        if len(question) < 3:
            answer = "Please send a question with at least 3 characters."
        else:
            try:
                answer, _ = answer_question(question, settings.default_top_k)
            except Exception:
                answer = "I could not complete that search. Check the RAG service configuration and try again."
    async with httpx.AsyncClient(timeout=20) as client:
        await client.post(
            f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
            json={"chat_id": chat_id, "text": answer[:4000]},
        )
