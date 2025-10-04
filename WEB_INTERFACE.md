# AI Hackathon Judge - Web Interface

## 🌐 Quick Start

Run the web application:

```bash
python web_app.py
```

Then open your browser to: **http://localhost:5000**

## ✨ Features

### 📤 Upload Interface
- **Drag & Drop**: Simply drag your ZIP file onto the upload area
- **Browse Files**: Click to open a file browser and select your submission
- **Real-time Progress**: Live progress bar showing analysis stages
- **Instant Results**: View report immediately after processing

### 📊 Reports Dashboard
- View all previously generated reports
- Sorted by creation date (newest first)
- One-click access to any report
- Clean, organized interface

### 🎨 Design
- **Midnight Purple Theme**: Consistent with the report styling
- **Responsive Layout**: Works on desktop, tablet, and mobile
- **Modern UI**: Card-based design with smooth animations
- **Dark Mode**: Easy on the eyes for extended use

## 🔧 Configuration

### Environment Variables
```bash
export GEMINI_API_KEY="your-api-key-here"  # Required for AI features
```

### Upload Limits
- Maximum file size: **500MB**
- Supported format: **ZIP files only**

## 📂 Directory Structure

```
data/
  web_uploads/        # Temporary uploaded files
  submissions/        # Processed submissions
reports/             # Generated HTML reports
web_templates/       # HTML templates for web interface
```

## 🚀 Usage

1. **Start the server**:
   ```bash
   python web_app.py
   ```

2. **Upload a submission**:
   - Go to http://localhost:5000
   - Drag and drop your ZIP file or click to browse
   - Click "Upload & Analyze"

3. **Monitor progress**:
   - Watch the real-time progress bar
   - See detailed status messages

4. **View results**:
   - Click "View Report" when complete
   - Report opens in a new tab

5. **Access previous reports**:
   - Click "View All Reports" from the homepage
   - Or go directly to http://localhost:5000/reports

## 🔒 Security Notes

- Files are stored temporarily in `data/web_uploads/`
- Each upload gets a unique job ID
- Server runs on localhost by default (change in web_app.py for network access)
- Consider adding authentication for production use

## ⚙️ Advanced Configuration

### Change Port
Edit `web_app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=8080)  # Change port here
```

### Enable Network Access
Change `host='0.0.0.0'` to allow connections from other devices on your network.

### Production Deployment
For production use:
```python
app.run(debug=False, host='127.0.0.1', port=5000)
```

Consider using a production WSGI server like Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 web_app:app
```

## 🎯 API Endpoints

- `GET /` - Homepage with upload form
- `POST /upload` - Upload and start processing
- `GET /status/<job_id>` - Check processing status
- `GET /report/<filename>` - View specific report
- `GET /reports` - List all reports

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Find and kill process on port 5000
# Windows:
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/Mac:
lsof -ti:5000 | xargs kill -9
```

### Upload Fails
- Check file size (max 500MB)
- Ensure it's a valid ZIP file
- Check available disk space

### Processing Hangs
- Check terminal output for errors
- Verify GEMINI_API_KEY is set
- Ensure all dependencies are installed

## 📝 Notes

- Processing time varies based on submission size and complexity
- Large submissions may take several minutes to analyze
- The progress bar updates every 2 seconds during processing
- Reports are cached - re-uploading the same file may skip analysis
