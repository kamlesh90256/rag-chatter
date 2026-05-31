"""Migration: persist synthetic timestamps for legacy chunks and reindex vector DB.

This script will:
- find Chunk rows missing timestamp_start/timestamp_end
- compute per-chunk synthetic timestamps per video using video.duration_seconds or default 60s
- update Chunk.timestamp_start/timestamp_end and metadata_json
- compute embeddings and upsert to vectorstore (Chroma or Qdrant) with updated metadata
"""
from sqlmodel import Session, select
import json
from backend.utils.database import engine
from backend.models.chunk import Chunk
from backend.models.video import Video
from backend.ingest.embeddings import embed_texts
from backend.vectorstore.factory import get_repository
from backend.ingest.pipeline import _serialize_video
from backend.utils.settings import get_settings

DEFAULT_DURATION = 60.0

def main():
    settings = get_settings()
    repo = get_repository()
    with Session(engine) as session:
        # find videos that have chunks missing timestamps
        stmt = select(Chunk.video_id).where(Chunk.timestamp_start == None)
        vids = {row[0] for row in session.exec(stmt)}
        stmt2 = select(Chunk.video_id).where(Chunk.timestamp_end == None)
        vids |= {row[0] for row in session.exec(stmt2)}
        if not vids:
            print('No legacy chunks missing timestamps found.')
            return
        print('Videos to fix:', vids)
        for vid in vids:
            chunks = list(session.exec(select(Chunk).where(Chunk.video_id == vid).order_by(Chunk.chunk_id)))
            if not chunks:
                continue
            video = session.get(Video, vid)
            duration = float(video.duration_seconds) if (video and video.duration_seconds) else DEFAULT_DURATION
            total = len(chunks) or 1
            per = duration / total
            texts = []
            metadatas = []
            ids = []
            for idx, chunk in enumerate(chunks, start=1):
                start = round((idx - 1) * per, 3)
                end = round(idx * per, 3)
                updated = False
                if chunk.timestamp_start is None or chunk.timestamp_end is None:
                    chunk.timestamp_start = start
                    chunk.timestamp_end = end
                    updated = True
                # update metadata_json
                try:
                    md = json.loads(chunk.metadata_json) if chunk.metadata_json else {}
                except Exception:
                    md = {}
                if md.get('timestamp_start') is None or md.get('timestamp_end') is None:
                    md['timestamp_start'] = chunk.timestamp_start
                    md['timestamp_end'] = chunk.timestamp_end
                    chunk.metadata_json = json.dumps(md)
                    updated = True
                if updated:
                    session.add(chunk)
                texts.append(chunk.text)
                # ensure metadata contains at least video_id, chunk_id
                md.setdefault('video_id', chunk.video_id)
                md.setdefault('chunk_id', chunk.chunk_id)
                md.setdefault('title', chunk.title)
                md.setdefault('creator', chunk.creator)
                md.setdefault('url', chunk.url)
                md['timestamp_start'] = chunk.timestamp_start
                md['timestamp_end'] = chunk.timestamp_end
                metadatas.append(md)
                ids.append(chunk.vector_id or chunk.id)
            session.commit()
            # compute embeddings and upsert to vector DB
            try:
                embeddings = embed_texts(texts)
            except Exception as exc:
                print('Embedding generation failed for video', vid, exc)
                embeddings = []
            try:
                if embeddings and len(embeddings) == len(texts):
                    repo.upsert_chunks(texts=texts, embeddings=embeddings, metadatas=metadatas, ids=ids)
                    print('Upserted', len(texts), 'chunks for', vid)
                else:
                    # if embeddings missing, attempt upsert with empty embeddings for metadata update (Chroma requires embeddings)
                    try:
                        repo.upsert_chunks(texts=texts, embeddings=[ [0.0]*settings.embedding_dim for _ in texts ], metadatas=metadatas, ids=ids)
                        print('Upserted placeholders for', vid)
                    except Exception as e:
                        print('Upsert to repo failed for', vid, e)
            except Exception as exc:
                print('Reindexing failed for', vid, exc)
    print('Migration complete.')

if __name__ == '__main__':
    main()
