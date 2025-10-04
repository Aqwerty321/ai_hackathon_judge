# AI Hackathon Judge

An extensible, explainable judging pipeline for AI hackathon submissions. It processes video presentations, written descriptions, and code repositories to produce transparent scores and reports.

## Features

- 🔍 **Modular analyzers** for video, text, and code signals.
- 🎥 **Video pipeline** with optional Whisper transcription + sentiment analysis and caching.
- 📝 **Text originality & claim checks** featuring similarity search, heuristics, and AI-generated detection fallbacks.
- 🧮 **Configurable weighting** of each modality to align with event priorities.
- 📝 **Explainable reports** saved to `reports/` summarising the decision process.
- ✅ **Unit tests** covering the scoring logic and heuristic analyzers.

## Repository Layout

```
ai_judge/
  main.py             # Entry point for the judging pipeline
  config.py           # Central configuration and weight management
  modules/            # Video, text, and code analyzers
  scoring/            # Score aggregation and reporting utilities
  utils/              # Shared helper functions

data/
  submissions/        # Project inputs (e.g., Project Alpha sample)
  similarity_corpus/  # Datasets for originality analysis
  intermediate_outputs/  # Working directory for cached artifacts

reports/              # Generated summary reports
models/               # Downloaded model artifacts
tests/                # Pytest-based unit tests
```

## Getting Started

1. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
2. Run the sample pipeline:
   ```powershell
   python -m ai_judge.main
   ```
3. Execute the test suite:
   ```powershell
   pytest
   ```

### Customising Judging Criteria

- Edit `config/judging_criteria.json` to tweak the criteria list, weights, and metric sources.
- Each `source` follows a dotted path into the analyzer outputs (e.g., `video.clarity_score`).
- Weights are auto-normalised at runtime, so you can provide any proportional values.
- Additional submission-level reports and a global `leaderboard.csv` are written to `reports/` after each run.

### Video Analysis Dependencies

- The video analyzer automatically uses Whisper + `transformers` sentiment models when available.
- Install optional extras to enable them fully:
   ```powershell
   pip install openai-whisper moviepy transformers
   ```
- Without these packages, the analyzer falls back to cached transcripts and lightweight heuristics.

### Text Analysis Extras

- Install embedding + detection helpers for deeper originality checks:
   ```powershell
   pip install sentence-transformers
   ```
- These dependencies are optional; without them, the analyzer still performs lexical similarity, claim heuristics, and AI-generated scoring based on rule-based signals.

#### Optional Local LLM Claim Verification

- To enrich claim analysis with a local instruction-tuned model, place `mistral-7b-instruct-v0.2.Q4_K_M.gguf` into the `models/` folder (already present via the setup steps).
- Install `ctransformers` for lightweight CPU inference:
   ```powershell
   pip install ctransformers
   ```
- Point the pipeline at the model by updating `Config` (or environment) with:
   - `text_llm_model_path`: relative or absolute path to the GGUF file
   - `text_llm_model_type`: model family name (e.g., `mistral`, `llama`)
   - `text_llm_max_tokens`: optional cap on generated reasoning tokens
- When configured, the analyzer augments each flagged claim with a verdict (`plausible`, `needs_verification`, `implausible`) and a brief rationale; it falls back silently to heuristics if loading fails.
- If you ever need to re-download it, authenticate with `huggingface-cli login`, install `huggingface_hub`, and run:
   ```powershell
   python - <<'PY'
from huggingface_hub import hf_hub_download
from pathlib import Path

path = hf_hub_download(
    repo_id="TheBloke/Mistral-7B-Instruct-v0.2-GGUF",
    filename="mistral-7b-instruct-v0.2.Q4_K_M.gguf",
)
dest = Path("models") / "mistral-7b-instruct-v0.2.Q4_K_M.gguf"
dest.parent.mkdir(parents=True, exist_ok=True)
if Path(path) != dest:
    dest.write_bytes(Path(path).read_bytes())
print(f"Model ready at {dest}")
PY
   ```

## Extending the Pipeline

- Replace the heuristic analyzers with ML-backed implementations.
- Expand `ScoreWeights` in `config.py` with additional modalities (e.g., business impact).
- Persist intermediate data to `data/intermediate_outputs/` for auditability.

## License

MIT License (update as needed for your event).
