from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from config import Config
import google.generativeai as genai

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = app.config['SECRET_KEY']

# Initialize Gemini AI
genai.configure(api_key=app.config['GEMINI_API_KEY'])
model = genai.GenerativeModel('gemini-1.5-flash')

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def analyze_document(filepath):
    """Analyze the document using Gemini AI"""
    try:
        # For text files
        if filepath.lower().endswith('.txt'):
            with open(filepath, 'r') as f:
                content = f.read()
        else:
            # For other file types (implement your specific processing)
            content = f"Contents of {os.path.basename(filepath)}"
        
        prompt = f"""Analyze this document for tax-related information:
        {content}
        Provide key findings and recommendations:"""
        
        response = model.generate_content(prompt)
        return response.text
    
    except Exception as e:
        return f"Error analyzing document: {str(e)}"

def generate_sample_data():
    """Generate sample data for dashboard and results"""
    return {
        'username': 'Test User',
        'salary_components': {
            'basic salary': 800000,
            'hra': 400000,
            'special allowance': 200000,
            'bonus': 100000
        },
        'deductions': {
            '80c': 150000,
            '80d': 25000,
            'home loan interest': 200000,
            'standard deduction': 50000
        },
        'tax_results': {
            'recommended_regime': 'new',
            'savings': 12500,
            'old_regime': {
                'taxable_income': 1200000,
                'tax': 187500
            },
            'new_regime': {
                'taxable_income': 1250000,
                'tax': 175000
            }
        },
        'documents': [
            {
                'filename': 'Form16.pdf',
                'summary': 'Form 16 for FY 2023-24 showing total income and taxes deducted',
                'content': '...extracted text from document...'
            }
        ]
    }

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    try:
        data = generate_sample_data()
        return render_template('dashboard.html', 
                             current_user={'name': data['username']},
                             **data)
    except Exception as e:
        app.logger.error(f"Dashboard error: {str(e)}")
        return render_template('500.html'), 500

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # Check if file was uploaded
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        
        # Check if filename is empty
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        # Validate file type
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            try:
                # Save the file
                file.save(filepath)
                
                # Get form data
                financial_year = request.form.get('financial_year', '2024-25')
                age_group = request.form.get('age_group', 'below_60')
                
                # Analyze the document
                analysis_result = analyze_document(filepath)
                
                # Generate sample results data
                results_data = generate_sample_data()
                results_data.update({
                    'filename': filename,
                    'financial_year': financial_year,
                    'age_group': age_group,
                    'analysis_text': analysis_result
                })
                
                return render_template('results.html', **results_data)
            
            except Exception as e:
                flash(f'Error processing file: {str(e)}', 'error')
                return redirect(request.url)
        
        flash('Invalid file type. Allowed types: ' + ', '.join(app.config['ALLOWED_EXTENSIONS']), 'error')
        return redirect(request.url)
    
    return render_template('upload.html')

@app.route('/analyze_documents', methods=['POST'])
def analyze_documents():
    """Alternative endpoint for form submission"""
    return upload()

# Other routes
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
        flash('Calculation complete', 'success')
        return redirect(url_for('results'))
    return render_template('calculator.html')

@app.route('/results')
def results():
    data = generate_sample_data()
    return render_template('results.html', **data)

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7860, debug=True)