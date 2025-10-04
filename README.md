# AI Hackathon Judge

An extensible, explainable judging pipeline for AI hackathon submissions. It processes video presentations, written descriptions, and code repositories to produce transparent scores and reports.

## Features

- 🔍 **Modular analyzers** for video, text, and code signals.
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

## Extending the Pipeline

- Replace the heuristic analyzers with ML-backed implementations.
- Expand `ScoreWeights` in `config.py` with additional modalities (e.g., business impact).
- Persist intermediate data to `data/intermediate_outputs/` for auditability.

## License

MIT License (update as needed for your event).
