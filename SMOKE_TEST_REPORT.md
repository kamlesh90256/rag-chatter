# Smoke Test Report

- **Backend health**: PASS — {"status": "ok", "timestamp": "2026-05-31T11:12:12.848892"}
- **YouTube ingestion**: PASS — {"id": "ddf34c64ab70ff1eca6082b7", "title": "Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster)", "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
- **Instagram ingestion**: PASS — {"id": "cb94e4ac8992490c5f514204", "title": "Video by anya_flix", "url": "https://www.instagram.com/reel/DY3lF6xSmqc/?igsh=MnZtajhyNzZoY2w4"}
- **Metadata extraction**: PASS — youtube={"title": "Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster)", "creator": "Rick Astley", "views": 1778044407}; instagram={"title": "Video by anya_flix", "creator": "Ann", "views": 0}
- **Transcript extraction**: PASS — youtube={"source_type": "yt-dlp+fallback-description", "chars": 2375}; instagram={"source_type": "yt-dlp+fallback-description", "chars": 88}
- **Engagement calculation**: PASS — {"youtube_rate": 1.21, "instagram_rate": 0.0, "winner": "Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster)"}
- **ChromaDB insertion**: PASS — youtube={"chunks": 3, "first_chunk": "The official video for “Never Gonna Give You Up” by Rick Astley. \n\nNever: The Autobiography 📚 OUT NOW! \nFollow this link"}; instagram={"chunks": 1, "first_chunk": "Achha koi nhi, tum reel hi like kr do😒🫣\n.\n.\n.\n.\n#shardasinha#song#newtrend#bihari#जितिया"}
- **Retrieval**: PASS — {"results": 4, "top": {"text": "The official video for “Never Gonna Give You Up” by Rick Astley. \n\nNever: The Autobiography 📚 OUT NOW! \nFollow this link to get your copy and listen to Rick’s ‘Never’ playlist ❤️ #Ri...
- **LangGraph memory**: PASS — {"first_answer": "(fallback) Based on retrieved context:\n[Source 1] Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster) |", "second_answer": "(fallback) Based on retrieved context:\n[Source 1] Rick A...
- **Streaming responses**: PASS — {"done": true, "answer": "(fallback) Based on retrieved context:\n[Source 1] Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster) |"}
- **Citations**: PASS — [{"video_id": "ddf34c64ab70ff1eca6082b7", "title": "Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster)", "creator": "Rick Astley", "chunk_id": 2, "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}...
