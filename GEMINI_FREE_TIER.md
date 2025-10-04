# Google Gemini Free Tier Setup Guide

## Quick Fix for Free Tier

The **free tier uses `gemini-pro`**, not `gemini-1.5-pro`. The default has been updated!

## ✅ Correct Usage (Free Tier)

### Option 1: Use Default (Recommended)
```powershell
# Set your API key
$env:GEMINI_API_KEY="your-api-key-here"

# Run normally - will use gemini-pro by default
python -m ai_judge.main --submission Student-Management-System-main.zip
```

### Option 2: Explicitly Specify Model
```powershell
python -m ai_judge.main --submission Student-Management-System-main.zip --gemini-model gemini-pro
```

## 🔍 Available Models by Tier

### Free Tier (API Key from makersuite.google.com)
- ✅ **`gemini-pro`** ← Default, works with free API keys
- ✅ **`gemini-pro-vision`** (for image inputs)

### Paid Tier (Requires billing enabled)
- 💰 `gemini-1.5-pro` (latest, most capable)
- 💰 `gemini-1.5-flash` (faster, cheaper)

## 🚨 Common Error

If you see:
```
[WARNING] Gemini API call failed: 404 models/gemini-1.5-pro is not found
```

**Solution:** You're using a free tier API key. The default is now `gemini-pro`, so just run without specifying a model:

```powershell
python -m ai_judge.main --submission your-project --no-cache
```

## 📊 Model Comparison

| Model | Tier | Speed | Quality | Cost |
|-------|------|-------|---------|------|
| `gemini-pro` | Free | Fast | Excellent | Free* |
| `gemini-1.5-pro` | Paid | Slower | Best | ~$7/1M tokens |
| `gemini-1.5-flash` | Paid | Fastest | Great | ~$0.35/1M tokens |

*Free tier limits: 60 requests/minute, 1,500 requests/day

## 🎯 Complete Example

```powershell
# Step 1: Get free API key from https://makersuite.google.com/app/apikey
# Step 2: Set environment variable
$env:GEMINI_API_KEY="AIzaSyC..."

# Step 3: Run pipeline (uses gemini-pro automatically)
python -m ai_judge.main --submission Student-Management-System-main.zip --no-cache

# Step 4: Check logs for confirmation
# Look for: [INFO] Generated combined summary using Gemini Pro API
```

## 💡 Verification

You should see in the logs:
```
[INFO] Generated combined summary using Gemini Pro API
```

If you still see warnings, double-check your API key at: https://makersuite.google.com/app/apikey

## 🆘 Troubleshooting

### Issue: 404 model not found
**Cause:** Using paid tier model with free tier key  
**Fix:** Use default (gemini-pro) or specify: `--gemini-model gemini-pro`

### Issue: 429 quota exceeded
**Cause:** Hit free tier limits (60/min or 1500/day)  
**Fix:** Wait or upgrade to paid tier

### Issue: Invalid API key
**Cause:** Wrong key or not enabled  
**Fix:** Get new key from https://makersuite.google.com/app/apikey

## 📝 Summary

- ✅ **Default model changed to `gemini-pro`** (free tier compatible)
- ✅ **No need to specify model** if using free tier
- ✅ **Automatic fallback to BART** if any Gemini issues
- ✅ **All existing functionality preserved**

**You're all set! Run the pipeline and enjoy better summaries with your free Gemini API key!** 🎉
