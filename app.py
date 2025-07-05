from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os
from config import Config
import google.generativeai as genai

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = app.config['SECRET_KEY']

# Initialize AI
genai.configure(api_key=app.config['GEMINI_API_KEY'])
model = genai.GenerativeModel('gemini-1.5-flash')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def process_document(filepath):
    """Implement your actual document processing logic here"""
    # Example: Use your AI model to analyze the document
    try:
        with open(filepath, 'rb') as f:
            response = model.generate_content(f.read())
        return response.text
    except Exception as e:
        return f"Analysis error: {str(e)}"

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html', username="User")

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
            
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            upload_folder = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
            os.makedirs(upload_folder, exist_ok=True)
            filepath = os.path.join(upload_folder, filename)
            file.save(filepath)
            
            # Process the file immediately
            analysis_result = process_document(filepath)
            return render_template('results.html', 
                                filename=filename,
                                result=analysis_result)
        
        flash('Invalid file type')
        return redirect(request.url)
    
    return render_template('upload.html')

@app.route('/results')
def results():
    # This route is just for displaying results from direct access
    flash('Please upload a document first')
    return redirect(url_for('upload'))

# Error Handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Create upload directory if it doesn't exist
    upload_dir = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
    os.makedirs(upload_dir, exist_ok=True)
    app.run(debug=True)