# Deprecation Notice: Local LLM Support Removed

**Date:** January 2025  
**Version:** Post-v1.0  

## Summary

This project has **completely migrated to Google Gemini AI** for all AI-powered features. Local LLM support (ctransformers, Mistral models, BART summarization) has been **deprecated and removed**.

## What Was Removed

### 1. **Local LLM (ctransformers + Mistral)**
- **Removed from:** `text_analyzer.py`, `config.py`, `main.py`
- **Previous usage:** Claim enrichment/verification
- **Replaced with:** Gemini API (`_enrich_claims_with_gemini`)
- **Reason:** Cloud-based AI provides better accuracy, no model downloads (~4GB+), simplified deployment

### 2. **BART Summarization**
- **Removed from:** `text_analyzer.py`
- **Previous usage:** Fallback for combined README + transcript summaries
- **Replaced with:** Gemini-only summaries
- **Reason:** User preference for cloud AI, eliminates large model download (~1.6GB)

### 3. **Configuration Fields**
Removed from `Config` dataclass:
- `text_llm_model_path`
- `text_llm_model_type`
- `text_llm_max_tokens`
- `text_llm_context_length`
- `text_llm_gpu_layers`
- `resolved_text_llm_model_path` property

### 4. **CLI Arguments**
Removed from `main.py`:
- `--llm-context`: Local LLM context window size
- `--llm-gpu-layers`: GPU layer offloading for local models

**Retained arguments** (still needed for other models):
- `--device`: Device preference for embeddings and AI detector
- `--ai-detector-context`: Context length for RoBERTa AI detector

## Migration Guide

### For Users

**Before (v1.0 - local LLM):**
```bash
python -m ai_judge --llm-context 4096 --llm-gpu-layers 32
```

**After (current - Gemini-only):**
```bash
# Set Gemini API key
set GEMINI_API_KEY=your_api_key_here

# Run with Gemini (default model: gemini-2.0-flash-lite)
python -m ai_judge

# Or specify model
python -m ai_judge --gemini-model models/gemini-2.5-flash
```

### For Developers

If you have custom code that references removed features:

1. **Claim Enrichment:** Replace `_enrich_claims_with_llm()` with `_enrich_claims_with_gemini()`
2. **Summaries:** Use `_generate_combined_summary()` (now Gemini-only, no BART fallback)
3. **Config:** Remove references to `text_llm_*` fields
4. **Models directory:** No longer needed for Mistral/GGUF files

## Why This Change?

1. **User Preference:** Explicit request to "make everything ai powered and deprecate local llm"
2. **Better Quality:** Gemini provides superior summaries and claim verification
3. **Simplified Deployment:** No need to download 4GB+ local models
4. **Free Tier Friendly:** Gemini free tier (60 req/min, 1,500 req/day) sufficient for most use cases
5. **Faster Iteration:** Cloud API updates without model re-downloads

## What Still Uses Local Models?

The following features **still use local Hugging Face models** and are NOT affected:
- **Embeddings:** `sentence-transformers/all-MiniLM-L6-v2` (similarity detection)
- **AI Detection:** `roberta-base-openai-detector` (AI content detection)

These models remain local because:
- Lightweight (~500MB combined)
- No API costs
- Fast inference
- Privacy-friendly (runs offline)

## Gemini Free Tier Limitations

- **Rate Limits:** 60 requests/minute, 1,500 requests/day
- **Models Available:** `gemini-2.0-flash-lite`, `gemini-2.5-flash`, etc. (40+ models)
- **Recommended Model:** `models/gemini-2.0-flash-lite` (fastest, lowest RECITATION rate)
- **Not Available:** `gemini-1.5-pro`, `gemini-pro` (Pro tier only)

## Rollback (If Needed)

If you need local LLM support, use **git history**:

```bash
# Find commit before deprecation
git log --oneline --grep="deprecate local llm"

# Checkout previous version
git checkout <commit_hash>
```

Or manually reinstall dependencies:
```bash
pip install ctransformers transformers[torch]
```

Then restore code from git history for:
- `ai_judge/modules/text_analyzer.py` (lines ~485-520)
- `ai_judge/config.py` (text_llm_* fields)
- `ai_judge/main.py` (--llm-context, --llm-gpu-layers args)

## Questions?

Contact the maintainer or open an issue on GitHub.

---

**Last Updated:** January 2025  
**Impact:** Breaking change for users relying on local LLM features  
**Workaround:** Use Gemini API (free tier available) or rollback via git
