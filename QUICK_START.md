# 🚀 AI Hackathon Judge - Quick Start Guide

## Launch the Web Interface

```bash
python web_app.py
```

Then open: **http://localhost:5000**

---

## Upload & Analyze

### Method 1: Drag & Drop
1. Drag your ZIP file from anywhere on your computer
2. Drop it onto the purple upload area
3. Click **"Upload & Analyze"**

### Method 2: File Browser
1. Click on the upload area
2. Browse to your ZIP file location
3. Select the file
4. Click **"Upload & Analyze"**

---

## Monitor Progress

Watch the progress bar fill up as your submission is analyzed:
- **0-20%**: Uploading and initializing
- **20-40%**: Video analysis
- **40-70%**: Text analysis and plagiarism checking
- **70-90%**: Code quality analysis
- **90-100%**: Generating report

Status messages show what's happening at each stage.

---

## View Results

When complete, you'll see a ✅ **Success** message.

Click **"View Report"** to open the full analysis in a new tab.

---

## View Previous Reports

From the homepage, click **"📊 View All Reports"** to see all generated reports sorted by date.

---

## Tips

- ✨ Max file size: **500MB**
- ✨ Only **ZIP files** are accepted
- ✨ Processing takes **1-3 minutes** per submission
- ✨ You can upload multiple submissions (one at a time)
- ✨ Reports are saved permanently in the `reports/` folder

---

## Troubleshooting

**"Upload failed"**
- Check file size (must be under 500MB)
- Ensure file is a valid ZIP
- Check available disk space

**"Processing failed"**
- Check terminal output for errors
- Verify `GEMINI_API_KEY` environment variable is set
- Try uploading again

**Server won't start**
- Port 5000 may be in use
- Close other applications using port 5000
- Or change the port in `web_app.py`

---

## Need Help?

Check the full documentation:
- **WEB_INTERFACE.md** - Detailed setup and configuration
- **WEB_IMPLEMENTATION_SUMMARY.md** - Technical details
- **README.md** - Overall project documentation

---

**Enjoy judging! 🏆**
