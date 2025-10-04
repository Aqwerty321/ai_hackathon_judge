# How to Fix: Gemini API Not Configured

## Problem
You're seeing this warning in your logs:
```
[WARNING] Gemini API not configured or failed; no combined summary available.
```

This means the `GEMINI_API_KEY` environment variable is not set, so Gemini-powered features are disabled:
- ❌ No AI code insights
- ❌ No combined text summary  
- ❌ No claim enrichment

## Solution: Set Your Gemini API Key

### Option 1: Set for Current PowerShell Session (Temporary)

```powershell
$env:GEMINI_API_KEY="your-actual-api-key-here"
```

Then restart the Flask server:
```powershell
python web_app.py
```

### Option 2: Set Permanently in PowerShell Profile

1. Edit your PowerShell profile:
```powershell
notepad $PROFILE
```

2. Add this line to the file:
```powershell
$env:GEMINI_API_KEY="your-actual-api-key-here"
```

3. Save and reload your profile:
```powershell
. $PROFILE
```

### Option 3: Set in Windows System Environment Variables (Permanent)

1. Open System Properties:
   - Press `Win + X` → System → Advanced system settings
   - Or search for "Environment Variables" in Start menu

2. Click "Environment Variables" button

3. Under "User variables", click "New"

4. Set:
   - Variable name: `GEMINI_API_KEY`
   - Variable value: `your-actual-api-key-here`

5. Click OK and restart your terminal

### Option 4: Create a .env File (Recommended for Development)

1. Create a file called `.env` in the project root:
```bash
GEMINI_API_KEY=your-actual-api-key-here
```

2. Update `web_app.py` to load from .env:
```python
# Add at the top of web_app.py
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file
```

3. Install python-dotenv:
```powershell
pip install python-dotenv
```

## How to Get a Gemini API Key

If you don't have a Gemini API key yet:

1. Go to: https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key (starts with `AIzaSy...`)
4. Use it in one of the methods above

## Verify It's Working

After setting the key, check if it's loaded:

```powershell
# In PowerShell
echo $env:GEMINI_API_KEY
```

Should output your API key (not empty).

Then restart the Flask server and upload a submission. You should see:

```
[INFO] ✓ Generated Gemini code insights (450 chars)
[INFO] Enriched 3 claims using Gemini AI
```

Instead of:

```
[WARNING] Gemini API not configured or failed; no combined summary available.
```

## Troubleshooting

### Key is set but still not working?

1. **Restart the Flask server** - Environment variables are loaded at startup
2. **Check the key is valid** - Try a test API call:
   ```powershell
   python check_gemini_models.py
   ```
3. **Check for typos** - Make sure there are no extra spaces or quotes
4. **Try a different model** - Add this to config if rate-limited:
   ```python
   config.gemini_model = "models/gemini-1.5-flash"
   ```

### Still seeing warnings?

Check logs for specific error messages:
- "API key not valid" → Get a new key
- "Resource exhausted" → Hit rate limit, wait or upgrade
- "Permission denied" → Enable Gemini API in Google Cloud Console

## Quick Fix for Right Now

Run this in PowerShell **before** starting the server:

```powershell
# Set the API key
$env:GEMINI_API_KEY="YOUR_KEY_HERE"

# Start the server
python web_app.py
```

Replace `YOUR_KEY_HERE` with your actual Gemini API key.

The server will then have access to Gemini features! 🎉
