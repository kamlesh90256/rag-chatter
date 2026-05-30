from langchain_core.prompts import ChatPromptTemplate

CHAT_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert creator-video analyst. Answer only with grounded claims from the supplied context. "
            "Always explain comparisons, mention engagement reasoning, and include citations using Source: Video Name | Chunk N. "
            "If the answer is not in the context, say that the available sources do not contain enough evidence.",
        ),
        (
            "human",
            "Question: {question}\n\nConversation memory:\n{memory}\n\nContext:\n{context}\n\nProvide a concise, evidence-based answer with source citations.",
        ),
    ]
)
