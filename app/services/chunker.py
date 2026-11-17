from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.config import settings


def split_text(text: str) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return [chunk for chunk in splitter.split_text(text) if chunk.strip()]
