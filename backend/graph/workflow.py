from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any, TypedDict

from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from sqlmodel import Session, select

from backend.models.chat_history import ChatHistory
from backend.models.video import Video
from backend.rag.context import build_context
from backend.rag.prompts import CHAT_PROMPT
from backend.rag.retrieval import RetrieverService
from backend.utils.settings import get_settings


class ChatState(TypedDict, total=False):
    question: str
    thread_id: str
    video_ids: list[str]
    memory: str
    retrieved_chunks: list[dict[str, Any]]
    context: str
    answer: str
    citations: list[dict[str, Any]]


@dataclass
class WorkflowResult:
    answer: str
    citations: list[dict[str, Any]]
    context: str


@lru_cache(maxsize=1)
def get_graph():
    settings = get_settings()
    memory = MemorySaver()
    llm = ChatOpenAI(
        model=settings.openai_model, api_key=settings.openai_api_key, temperature=0.2
    )
    retriever = RetrieverService()

    def load_memory(state: ChatState) -> ChatState:
        return {
            "memory": _load_conversation_memory(
                state.get("thread_id", "default"), state.get("video_ids")
            )
        }

    def retrieve(state: ChatState) -> ChatState:
        chunks = retriever.retrieve(
            state["question"], video_ids=state.get("video_ids"), k=settings.retriever_k
        )
        return {"retrieved_chunks": chunks}

    def build(state: ChatState) -> ChatState:
        context = build_context(state.get("retrieved_chunks", []))
        citations = [
            {
                "video_id": chunk.get("metadata", {}).get("video_id"),
                "title": chunk.get("metadata", {}).get("title", "Unknown title"),
                "creator": chunk.get("metadata", {}).get("creator", "Unknown creator"),
                "chunk_id": chunk.get("metadata", {}).get("chunk_id"),
                "url": chunk.get("metadata", {}).get("url"),
            }
            for chunk in state.get("retrieved_chunks", [])
        ]
        return {"context": context, "citations": citations}

    def answer(state: ChatState) -> ChatState:
        messages = CHAT_PROMPT.format_messages(
            question=state["question"],
            memory=state.get("memory", ""),
            context=state.get("context", ""),
        )
        try:
            response = llm.invoke(messages)
            return {"answer": response.content}
        except Exception:
            # Fallback: build a deterministic answer from the provided context
            ctx = state.get("context", "")
            citations = state.get("retrieved_chunks", [])
            summary = (
                (ctx[:1000] + "...") if len(ctx) > 1000 else ctx
            )
            citation_list = (
                "\n".join(
                    f"- {c.get('metadata', {}).get('title','Unknown title')} ({c.get('metadata', {}).get('creator','')})"
                    for c in citations
                )
                or "No citations"
            )
            answer = (
                f"(fallback) Based on retrieved context:\n{summary}\n\nCitations:\n{citation_list}"
            )
            return {"answer": answer}

    graph = StateGraph(ChatState)
    graph.add_node("load_memory", load_memory)
    graph.add_node("retrieve", retrieve)
    graph.add_node("build", build)
    graph.add_node("answer", answer)
    graph.add_edge(START, "load_memory")
    graph.add_edge("load_memory", "retrieve")
    graph.add_edge("retrieve", "build")
    graph.add_edge("build", "answer")
    graph.add_edge("answer", END)
    return graph.compile(checkpointer=memory)


def _load_conversation_memory(thread_id: str, video_ids: list[str] | None) -> str:
    from backend.utils.database import engine

    with Session(engine) as session:
        filters = [ChatHistory.thread_id == thread_id]
        histories = list(
            session.exec(
                select(ChatHistory)
                .where(*filters)
                .order_by(ChatHistory.created_at.desc())
                .limit(12)
            )
        )
        videos = list(
            session.exec(select(Video).order_by(Video.created_at.desc()).limit(2))
        )
    transcript_lines = [f"{item.role}: {item.content}" for item in reversed(histories)]
    if videos:
        transcript_lines.append(
            "Relevant videos: "
            + ", ".join(f"{video.title} by {video.creator}" for video in videos)
        )
    if video_ids:
        transcript_lines.append("Requested video_ids: " + ", ".join(video_ids))
    return "\n".join(transcript_lines)


def run_workflow(
    question: str, thread_id: str, video_ids: list[str] | None = None
) -> WorkflowResult:
    graph = get_graph()
    state = graph.invoke(
        {"question": question, "thread_id": thread_id, "video_ids": video_ids},
        config={"configurable": {"thread_id": thread_id}},
    )
    return WorkflowResult(
        answer=state["answer"],
        citations=state.get("citations", []),
        context=state.get("context", ""),
    )
