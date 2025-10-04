# AI-Powered Combined Summary Feature

## Overview

The AI Judge pipeline now generates intelligent combined summaries that merge information from both the project's README/description and the video presentation transcript. This provides richer, more comprehensive project understanding using transformer-based NLP.

## Implementation

### Components Added

1. **TextAnalyzer Enhancement** (`ai_judge/modules/text_analyzer.py`):
   - New field: `combined_summary: str | None` in `TextAnalysisResult`
   - New method: `_generate_combined_summary(description, transcript)` - Uses facebook/bart-large-cnn model
   - New method: `_merge_texts(description, transcript)` - Intelligently combines description and transcript
   - Updated `analyze()` signature to accept optional `transcript` parameter

2. **Main Pipeline Integration** (`ai_judge/main.py`):
   - Updated text analyzer call to pass video transcript: `text_analyzer.analyze(submission_dir, video_result.transcript)`

3. **Report Template Update** (`ai_judge/templates/submission_report.html.j2`):
   - Added prominent AI-powered summary section with special styling
   - Positioned between charts and traditional summary for maximum visibility

4. **Test Coverage** (`tests/test_text_analyzer.py`):
   - New test: `test_combined_summary_generation()` - Verifies summary generation and content quality

## How It Works

1. **Text Merging**: The system combines project description and video transcript:
   ```
   Project Description: {README content}
   
   Presentation Transcript: {video transcript}
   ```

2. **AI Summarization**: Uses facebook/bart-large-cnn (CNN/Daily Mail fine-tuned BART model):
   - Truncates input to 4096 characters if needed
   - Generates 40-150 token summary
   - Runs on configured device (CPU/CUDA/MPS)

3. **Smart Fallbacks**:
   - If no transcript available, uses description only
   - If description empty but transcript exists, uses transcript only
   - Returns None if both are empty

## Report Display

The combined summary appears in a highlighted blue section:

```
🤖 AI-Powered Project Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[AI-generated summary combining README and presentation]
```

## Example Output

For the Student Management System project:
> "A simple Student Management System built in Java to manage student records including adding, updating, deleting, and displaying student details. This project demonstrates the core concepts of object-oriented programming (OOP) and file handling in Java."

## Performance

- **Model**: facebook/bart-large-cnn (~1.63 GB)
- **Execution Time**: ~2-5 seconds on CPU (included in text analysis stage)
- **Context Limit**: 4096 characters input, 40-150 tokens output
- **Device Support**: CPU, CUDA, MPS (Apple Silicon)

## Benefits

1. **Richer Understanding**: Combines written documentation with spoken presentation
2. **Concise Overview**: Transformer model produces coherent, readable summaries
3. **Deterministic**: Same input produces same output (good for reproducibility)
4. **Automated**: No manual summary writing needed

## Configuration

The feature uses existing device configuration:
```bash
# Use GPU if available
python -m ai_judge.main --submission <name> --device cuda

# Force CPU
python -m ai_judge.main --submission <name> --device cpu
```

## Dependencies

- `transformers` (Hugging Face)
- `torch` (PyTorch)
- Model: `facebook/bart-large-cnn` (auto-downloaded on first run)

## Testing

Run the test suite to verify:
```bash
pytest tests/test_text_analyzer.py::test_combined_summary_generation -v
```

All 24 tests pass including the new combined summary test.

## Future Enhancements

Potential improvements:
1. Support for multiple summary lengths (short/medium/long)
2. Configurable summarization models (T5, LED, etc.)
3. Multi-language summary support
4. Summary caching to avoid regeneration
5. Comparison with human-written summaries

## Technical Notes

- Summary generation is optional - pipeline works even if it fails
- Model weights are cached after first download (~1.6 GB)
- Uses same device resolution as other ML components
- Truncation warnings are expected and can be safely ignored
