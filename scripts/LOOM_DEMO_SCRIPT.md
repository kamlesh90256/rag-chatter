Loom Demo Script — End-to-end validation walkthrough

1. Intro (5s)
 - Show the app landing page (open `http://127.0.0.1:3001`).

2. Ingest / Comparison (20s)
 - Enter two video URLs (YouTube + Instagram) and click `Build comparison`.
 - Show the `Comparison metrics` section (screenshot available at `scripts/validation_output/frontend_comparison_full.png`).

3. Chat + Citations (30s)
 - Ask: "Why did Video A outperform Video B?"
 - Show the chat response and citation panel (validation HTML generated at `scripts/validation_output/results_with_timestamps.html`).

4. Memory (10s)
 - Ask a follow-up question in the same thread and highlight the memory snapshot (`scripts/validation_output/memory.json`).

5. Notes for the demo
 - Explain that timestamps were missing for some transcripts; for the demo we synthesized timestamps to show citations with time ranges. The production fix is to enable timestamped transcripts or run a forced alignment step.

Files to attach when recording
 - `scripts/validation_output/frontend_comparison_full.png`
 - `scripts/validation_output/results_with_timestamps.html`
 - `scripts/validation_output/chat_results.json`
