from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os
from config import Config
import google.generativeai as genai

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize Gemini AI
genai.configure(api_key=app.config['GEMINI_API_KEY'])
model = genai.GenerativeModel('gemini-1.5-flash')

# Helper Functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Main Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# Document Handling Routes
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'danger')
            return redirect(request.url)
        
        files = request.files.getlist('file')
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Save file and process (implementation needed)
                flash(f'File {filename} uploaded successfully', 'success')
            else:
                flash('Invalid file type', 'danger')
        return redirect(url_for('dashboard'))
    return render_template('upload.html')

# Tax Services Routes
@app.route('/calculator', methods=['GET', 'POST'])
def calculator():
    if request.method == 'POST':
        # Process calculator form data
        return redirect(url_for('results'))
    return render_template('calculator.html')

@app.route('/results')
def results():
    return render_template('results.html')

# GST Routes
@app.route('/gst')
def gst():
    return render_template('gst.html')

# Investments Routes
@app.route('/investments')
def investments():
    return render_template('investments.html')

# Advisory Routes
@app.route('/advisory')
def advisory():
    return render_template('advisory/resources.html')

# AI Assistant Route
@app.route('/ask_gemini', methods=['POST'])
def ask_gemini():
    if not request.is_json:
        return {"error": "Request must be JSON"}, 400
    
    data = request.get_json()
    user_question = data.get('question')
    context = data.get('context', '')
    
    prompt = f"""As a professional tax advisor, provide accurate information about:
    {context}
    Question: {user_question}
    Include relevant tax sections when applicable."""
    
    try:
        response = model.generate_content(prompt)
        return {"response": response.text}
    except Exception as e:
        return {"error": str(e)}, 500

# Error Handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)