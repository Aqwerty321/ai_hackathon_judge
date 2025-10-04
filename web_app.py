"""
Flask web application for AI Hackathon Judge.
Provides a web interface for uploading submissions and viewing results.
"""
from __future__ import annotations

import logging
import os
import shutil
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Dict

from flask import Flask, render_template, request, jsonify, send_file, url_for
from werkzeug.utils import secure_filename

from ai_judge.config import Config
from ai_judge.main import run_pipeline
from ai_judge.utils.file_helpers import ensure_directory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)
LOGGER = logging.getLogger(__name__)

app = Flask(__name__, template_folder='web_templates', static_folder='web_static')
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size
app.config['UPLOAD_FOLDER'] = Path('data/web_uploads')
app.config['SECRET_KEY'] = os.urandom(24)


@app.template_filter('format_timestamp')
def format_timestamp(timestamp):
    """Format Unix timestamp to readable date."""
    from datetime import datetime
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime('%Y-%m-%d %H:%M:%S')

# Global state for tracking processing jobs
processing_jobs: Dict[str, Dict[str, Any]] = {}
jobs_lock = threading.Lock()


def allowed_file(filename: str) -> bool:
    """Check if the uploaded file is a zip file."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'zip'


def process_submission_async(job_id: str, zip_path: Path, submission_name: str):
    """Process a submission in a background thread."""
    try:
        with jobs_lock:
            processing_jobs[job_id]['status'] = 'processing'
            processing_jobs[job_id]['progress'] = 10
            processing_jobs[job_id]['message'] = 'Initializing...'
        
        # Create config
        config = Config()
        config.gemini_api_key = os.environ.get("GEMINI_API_KEY")
        
        # Ensure the submission is in the right location
        submissions_dir = Path('data/submissions')
        ensure_directory(submissions_dir)
        
        # Copy zip to submissions directory if not already there
        target_zip = submissions_dir / zip_path.name
        if not target_zip.exists():
            shutil.copy2(zip_path, target_zip)
        
        # Update progress
        with jobs_lock:
            if job_id in processing_jobs:
                processing_jobs[job_id]['progress'] = 20
                processing_jobs[job_id]['message'] = 'Running analysis pipeline...'
        
        # Run the pipeline
        result = run_pipeline(
            config=config,
            submission_name=submission_name,
        )
        
        # Extract report path from first submission
        report_path = None
        if result.get('submissions') and len(result['submissions']) > 0:
            report_path = result['submissions'][0].get('report_path')
        
        with jobs_lock:
            processing_jobs[job_id]['status'] = 'completed'
            processing_jobs[job_id]['progress'] = 100
            processing_jobs[job_id]['message'] = 'Processing complete!'
            processing_jobs[job_id]['report_path'] = str(report_path) if report_path else None
            processing_jobs[job_id]['submission_name'] = submission_name
            
    except Exception as e:
        LOGGER.error(f"Error processing submission {job_id}: {e}", exc_info=True)
        with jobs_lock:
            processing_jobs[job_id]['status'] = 'error'
            processing_jobs[job_id]['message'] = f'Error: {str(e)}'


@app.route('/')
def index():
    """Render the homepage with upload form."""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and start processing."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Only ZIP files are allowed'}), 400
    
    try:
        # Create upload directory if it doesn't exist
        app.config['UPLOAD_FOLDER'].mkdir(parents=True, exist_ok=True)
        
        # Save the uploaded file
        filename = secure_filename(file.filename)
        job_id = f"{int(time.time())}_{filename}"
        zip_path = app.config['UPLOAD_FOLDER'] / filename
        file.save(zip_path)
        
        # Initialize job tracking
        submission_name = filename.rsplit('.', 1)[0]
        with jobs_lock:
            processing_jobs[job_id] = {
                'status': 'queued',
                'progress': 0,
                'message': 'Upload complete, queued for processing...',
                'submission_name': submission_name,
            }
        
        # Start processing in background thread
        thread = threading.Thread(
            target=process_submission_async,
            args=(job_id, zip_path, submission_name),
            daemon=True
        )
        thread.start()
        
        return jsonify({
            'job_id': job_id,
            'message': 'Upload successful, processing started',
        })
        
    except Exception as e:
        LOGGER.error(f"Upload error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/status/<job_id>')
def check_status(job_id: str):
    """Check the processing status of a job."""
    with jobs_lock:
        if job_id not in processing_jobs:
            return jsonify({'error': 'Job not found'}), 404
        
        job = processing_jobs[job_id]
        return jsonify({
            'status': job['status'],
            'progress': job['progress'],
            'message': job['message'],
            'report_path': job.get('report_path'),
            'submission_name': job.get('submission_name'),
        })


@app.route('/report/<path:filename>')
def view_report(filename: str):
    """Serve the generated HTML report."""
    report_path = Path('reports') / filename
    if not report_path.exists():
        return "Report not found", 404
    
    return send_file(report_path, mimetype='text/html')


@app.route('/reports')
def list_reports():
    """List all available reports."""
    reports_dir = Path('reports')
    if not reports_dir.exists():
        return render_template('reports_list.html', reports=[])
    
    reports = []
    for report_file in reports_dir.glob('*_report.html'):
        reports.append({
            'name': report_file.stem.replace('_report', ''),
            'filename': report_file.name,
            'modified': report_file.stat().st_mtime,
        })
    
    reports.sort(key=lambda x: x['modified'], reverse=True)
    return render_template('reports_list.html', reports=reports)


if __name__ == '__main__':
    # Ensure directories exist
    Path('data/web_uploads').mkdir(parents=True, exist_ok=True)
    Path('reports').mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*60)
    print("🚀 AI Hackathon Judge - Web Interface")
    print("="*60)
    print(f"📂 Upload folder: {Path('data/web_uploads').absolute()}")
    print(f"📊 Reports folder: {Path('reports').absolute()}")
    print(f"🌐 Starting server at: http://localhost:5000")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
