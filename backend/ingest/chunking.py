from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.utils.settings import get_settings


def chunk_transcript(text: str) -> list[str]:
    settings = get_settings()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap
    )
    return splitter.split_text(text)
