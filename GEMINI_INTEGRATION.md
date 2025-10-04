# Gemini Pro Integration Guide

## Overview

The AI Judge pipeline now supports **Google Gemini Pro API** for generating AI-powered combined summaries. Gemini Pro is given **highest priority** over local LLM models, providing:

- ✅ **Better Quality**: State-of-the-art language understanding from Google's latest models
- ✅ **Faster Performance**: No local model loading/inference overhead
- ✅ **Lighter Deployment**: No need to download 1.6GB+ BART models
- ✅ **Scalability**: Cloud-based API scales automatically

## Priority Order

When generating combined summaries, the system uses this priority:

1. **🥇 Google Gemini Pro API** (if API key provided) ← **HIGHEST PRIORITY**
2. **🥈 Local BART Model** (facebook/bart-large-cnn fallback)

## Setup

### 1. Get Your Gemini API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Copy your API key

### 2. Configure the API Key

You have two options:

#### Option A: Environment Variable (Recommended)

**Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY="your-api-key-here"
```

**Windows (cmd):**
```cmd
set GEMINI_API_KEY=your-api-key-here
```

**Linux/Mac:**
```bash
export GEMINI_API_KEY="your-api-key-here"
```

To make it permanent, add to your shell profile (~/.bashrc, ~/.zshrc, etc.)

#### Option B: Command-Line Argument

```bash
python -m ai_judge.main --submission <name> --gemini-api-key "your-api-key-here"
```

### 3. Run the Pipeline

Once configured, simply run the pipeline normally:

```bash
python -m ai_judge.main --submission Student-Management-System-main.zip
```

The system will automatically use Gemini Pro for generating summaries!

## Configuration Options

### CLI Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--gemini-api-key` | Your Gemini API key | From `GEMINI_API_KEY` env var |
| `--gemini-model` | Gemini model to use | `gemini-1.5-pro` |

### Available Models

- `gemini-1.5-pro` (default) - Latest production model
- `gemini-1.5-flash` - Faster, more cost-effective
- `gemini-pro` - Legacy stable version

### Example Commands

**Using environment variable:**
```bash
$env:GEMINI_API_KEY="AIzaSyC..."; python -m ai_judge.main --submission project_alpha
```

**Using CLI argument:**
```bash
python -m ai_judge.main --submission project_alpha --gemini-api-key "AIzaSyC..."
```

**Using different model:**
```bash
python -m ai_judge.main --submission project_alpha --gemini-model gemini-1.5-flash
```

**No cache with Gemini:**
```bash
python -m ai_judge.main --submission project_alpha --no-cache
```

## How It Works

### Summary Generation Process

1. **Input Preparation**: System combines project description (README) and video transcript
2. **Gemini API Call**: Sends combined text with a specialized prompt:
   ```
   Please provide a concise, professional summary of the following project 
   information in 2-3 sentences. Focus on the main purpose, key features, 
   and technology used.
   ```
3. **Response Processing**: Cleans up markdown formatting, returns clean summary
4. **Fallback**: If Gemini fails or API key not provided, falls back to local BART model

### API Parameters

The integration uses these Gemini parameters for optimal results:

```python
{
    "temperature": 0.3,        # Lower = more deterministic
    "top_p": 0.8,             # Nucleus sampling
    "top_k": 40,              # Top-k sampling
    "max_output_tokens": 200  # Roughly 2-3 sentences
}
```

## Verification

To verify Gemini is being used, check the logs:

```
[INFO] Generated combined summary using Gemini Pro API  ← Success!
```

If you see this instead:
```
[INFO] Generated combined summary using local BART model
```

Then Gemini wasn't used (check your API key).

## Troubleshooting

### Error: "Gemini API call failed"

**Possible causes:**
1. Invalid API key
2. API quota exceeded
3. Network connectivity issues
4. API region restrictions

**Solution:**
- Verify your API key at [Google AI Studio](https://makersuite.google.com/app/apikey)
- Check your quota limits
- System will automatically fall back to local BART model

### Error: "No module named 'google.generativeai'"

**Solution:**
```bash
pip install google-generativeai
```

Or:
```bash
pip install -r requirements.txt
```

### Gemini Not Being Used

**Check:**
1. Environment variable set: `echo $env:GEMINI_API_KEY` (PowerShell)
2. API key passed via CLI
3. No errors in logs (run with `--no-cache` to force regeneration)

### API Key Security

**⚠️ Security Best Practices:**

1. **Never commit API keys to git**
   - Add to `.gitignore`: `*.env`, `.env.*`
   - Use environment variables

2. **Restrict API key permissions**
   - Use application restrictions in Google Cloud Console
   - Set IP allowlists if possible

3. **Rotate keys regularly**
   - Generate new keys periodically
   - Revoke old keys

4. **Monitor usage**
   - Check quota at [Google Cloud Console](https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/quotas)

## Cost & Quotas

### Free Tier (as of 2025)

- **60 requests per minute**
- **1,500 requests per day**
- **1 million tokens per day**

For typical hackathon projects:
- Each summary uses ~500-1,000 input tokens + ~50-100 output tokens
- **You can process 1,000+ submissions daily on free tier**

### Pricing (Paid Tier)

If you exceed free tier:
- Input: $0.35 per million tokens
- Output: $1.05 per million tokens

**Typical project cost: $0.0005 - $0.001 per submission**

Check current pricing: [Google AI Pricing](https://ai.google.dev/pricing)

## Benefits Over Local Models

| Feature | Gemini Pro | Local BART |
|---------|------------|------------|
| **Quality** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Speed** | ~1-2s | ~2-5s |
| **Setup** | API key only | 1.6GB download |
| **Memory** | 0MB | ~2GB RAM |
| **Cost** | $0.001/submission | Free but slower |
| **Offline** | ❌ | ✅ |

## Example Output

### With Gemini Pro:

> "This Student Management System is a Java-based application designed to manage student records through CRUD operations. It features a command-line interface for adding, updating, deleting, and searching student information, with optional file-based persistence. The project demonstrates core OOP concepts including encapsulation and inheritance."

### With Local BART:

> "A simple Student Management System built in Java to manage student records including adding, updating, deleting, and displaying student details. This project demonstrates the core concepts of object-oriented programming (OOP) and file handling in Java."

**Both are good, but Gemini provides more structured, detailed summaries!**

## Advanced Configuration

### Custom Prompt Template

You can modify the prompt in `ai_judge/modules/text_analyzer.py`:

```python
def _generate_summary_with_gemini(self, text: str) -> str | None:
    prompt = f"""Your custom prompt here
    
{text}

Summary:"""
```

### Adjust Response Length

Modify `max_output_tokens` in the Gemini call:

```python
generation_config={
    "max_output_tokens": 300,  # Longer summaries
}
```

### Change Model Globally

Update `config.py`:

```python
gemini_model: str = "gemini-1.5-flash"  # Faster, cheaper
```

## Testing

### Test Gemini Integration

```python
# In tests/test_text_analyzer.py
def test_gemini_summary_generation():
    analyzer = TextAnalyzer(
        gemini_api_key="your-test-key",
        gemini_model="gemini-1.5-pro"
    )
    result = analyzer.analyze(submission_dir, transcript="...")
    assert result.combined_summary is not None
```

### Mock Gemini for Unit Tests

```python
from unittest.mock import Mock, patch

@patch('ai_judge.modules.text_analyzer.genai')
def test_with_mock_gemini(mock_genai):
    mock_model = Mock()
    mock_model.generate_content.return_value.text = "Test summary"
    mock_genai.GenerativeModel.return_value = mock_model
    # ... test code
```

## Migration Guide

### From Local BART Only

**Before:**
```bash
python -m ai_judge.main --submission project_alpha
# Uses BART (slow, but offline)
```

**After:**
```bash
$env:GEMINI_API_KEY="your-key"
python -m ai_judge.main --submission project_alpha
# Uses Gemini (fast, requires internet)
```

### Hybrid Deployment

For production, you might want:
- **Online**: Use Gemini for speed and quality
- **Offline/Backup**: BART automatically kicks in if Gemini unavailable

This is **already built-in** - no changes needed!

## FAQ

**Q: Do I need a credit card for Gemini API?**
A: No! Free tier doesn't require billing. You only need a Google account.

**Q: Will my data be used to train Gemini models?**
A: No. Per Google's policy, API inputs are not used for model training.

**Q: Can I use Gemini for claim verification too?**
A: Currently only for summaries. Claim verification uses DuckDuckGo search.

**Q: What happens if I run out of quota?**
A: System automatically falls back to local BART model. No failures!

**Q: Can I use other models like GPT-4?**
A: Not yet, but the architecture supports it. Contribution welcome!

## Support

- **Gemini API Issues**: [Google AI Support](https://ai.google.dev/docs)
- **Pipeline Issues**: Check project README or open GitHub issue
- **API Key Problems**: [Google Cloud Console](https://console.cloud.google.com/)

## Summary

1. Get API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Set `GEMINI_API_KEY` environment variable
3. Run pipeline normally
4. Enjoy better, faster summaries! 🚀

**Gemini Pro is now your default summarization engine with automatic BART fallback!**
