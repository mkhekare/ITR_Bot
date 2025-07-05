from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os
from config import Config
import google.generativeai as genai

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = app.config['SECRET_KEY']

# Initialize Gemini AI
genai.configure(api_key=app.config['GEMINI_API_KEY'])
model = genai.GenerativeModel('gemini-1.5-flash')

# Helper Functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def process_uploaded_file(file):
    """Process the uploaded file and return analysis results"""
    try:
        # For text files
        if file.filename.lower().endswith('.txt'):
            text = file.read().decode('utf-8')
        
        # For other files (PDF, images), you'll need additional libraries
        # This is a placeholder - implement your actual processing
        else:
            text = f"File content analysis for {file.filename}"
        
        # Analyze with Gemini
        prompt = f"""Analyze this document for tax-related information:
        {text}
        Provide key findings and recommendations:"""
        
        response = model.generate_content(prompt)
        return response.text
    
    except Exception as e:
        return f"Error processing file: {str(e)}"

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
            flash('No file selected')
            return redirect(request.url)
            
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            
            # Process file directly without saving
            analysis_result = process_uploaded_file(file)
            
            return render_template('results.html',
                                filename=filename,
                                result=analysis_result)
        
        flash('Invalid file type. Allowed types: ' + ', '.join(app.config['ALLOWED_EXTENSIONS']))
        return redirect(request.url)
    
    return render_template('upload.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')

@app.route('/gst')
def gst():
    return render_template('gst.html')

@app.route('/investments')
def investments():
    return render_template('investments.html')

@app.route('/calculator', methods=['GET', 'POST'])
def calculator():
    if request.method == 'POST':
        # Process form data
        flash('Calculation complete')
        return redirect(url_for('results'))
    return render_template('calculator.html')

@app.route('/results')
def results():
    return render_template('results.html')

# Error Handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Create upload directory if configured
    if hasattr(app.config, 'UPLOAD_FOLDER'):
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)