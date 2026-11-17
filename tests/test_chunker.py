from app.services.chunker import split_text


def test_split_text_returns_chunks():
    text = ("Retrieval augmented generation combines retrieval with language models. " * 50).strip()
    chunks = split_text(text)
    assert len(chunks) > 1
    assert all(chunk.strip() for chunk in chunks)


def test_split_text_empty_input():
    assert split_text("") == []
