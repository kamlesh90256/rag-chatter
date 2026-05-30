# Loom Demo Script

## Opening

Show the dashboard and explain that the platform compares a YouTube video and an Instagram Reel, then answers evidence-backed questions with citations.

## Step 1: Input URLs

Say:

- "I’ll paste one YouTube URL and one Instagram Reel URL."
- "The backend validates the URLs before ingesting anything."

Actions:

- Paste the YouTube URL.
- Paste the Instagram Reel URL.
- Click **Build comparison**.

## Step 2: Metadata

Say:

- "The system extracts title, creator, views, likes, comments, upload date, duration, hashtags, and follower count."
- "This metadata is stored alongside the transcript and chunk records."

Show:

- Video A card
- Video B card

## Step 3: Transcript Extraction

Say:

- "For YouTube, transcript lookup is attempted first."
- "If the transcript is missing, the system falls back to yt-dlp plus Whisper."
- "Instagram follows the fallback flow because transcript APIs are often unavailable."

Show the comparison cards and hook analysis area.

## Step 4: Embeddings and Retrieval

Say:

- "Each transcript is chunked at 800 characters with 100 characters of overlap."
- "The chunks are embedded with OpenAI text-embedding-3-small and stored in ChromaDB."
- "When I ask a question, the retriever pulls the most relevant chunks back into context."

Ask:

- "Why did Video A outperform Video B?"
- "Compare hooks."
- "Compare first 5 seconds."

## Step 5: Memory and Streaming

Say:

- "LangGraph MemorySaver keeps the conversation state around between questions."
- "The answer streams back over Server-Sent Events."

Show:

- typing indicator / streaming response
- conversation history panel

## Step 6: Citations

Say:

- "Every answer includes citations in the form Source: Video Name | Chunk N."
- "You can trace each claim back to a specific chunk from the underlying transcript."

Show:

- Source panel
- citation cards

## Step 7: Hook Analysis

Say:

- "The platform scores the first five seconds using hook, curiosity, emotion, retention, and CTA signals on a 0 to 100 scale."
- "These scores help creators quickly see what is working and what needs to change."

## Step 8: Scaling Explanation

Say:

- "This architecture can scale to about 1000 creators per day by moving ingestion into background workers, adding Redis caching, batching embeddings, and migrating the vector store to Qdrant when needed."

Close with:

- "The system is designed so the analysis remains grounded, explainable, and traceable even as usage grows."
