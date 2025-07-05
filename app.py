from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
import os
import time
from config import Config
import google.generativeai as genai

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = app.config['SECRET_KEY']

# Initialize AI
genai.configure(api_key=app.config['GEMINI_API_KEY'])
model = genai.GenerativeModel('gemini-1.5-flash')

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def analyze_content(content):
    """Analyze content with Gemini AI"""
    prompt = """Analyze this tax document and provide:
    1. Salary components with amounts
    2. Deductions with amounts
    3. Tax regime recommendations
    
    Document Content:
    {content}"""
    
    try:
        response = model.generate_content(prompt.format(content=content))
        return response.text
    except Exception as e:
        return f"Analysis error: {str(e)}"

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'files' not in request.files:
            return jsonify({'error': 'No file selected'}), 400
        
        files = request.files.getlist('files')
        if not files or files[0].filename == '':
            return jsonify({'error': 'No files selected'}), 400

        try:
            # Process first file only for demo
            file = files[0]
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                # Simulate processing delay
                time.sleep(2)
                
                # Generate sample response (replace with actual analysis)
                result = {
                    'status': 'success',
                    'redirect': url_for('results'),
                    'financial_year': request.form.get('financial_year'),
                    'age_group': request.form.get('age_group')
                }
                return jsonify(result)
            
            return jsonify({'error': 'Invalid file type'}), 400
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return render_template('upload.html')

@app.route('/results')
def results():
    # Sample data - replace with actual processed data
    data = {
        'filename': 'Sample_Document.pdf',
        'extracted_data': {
            'salary_components': {
                'basic_salary': 800000,
                'hra': 400000,
                'special_allowance': 200000
            },
            'deductions': {
                '80C': 150000,
                '80D': 25000
            }
        },
        'tax_results': {
            'recommended_regime': 'new',
            'savings': 12500,
            'old_regime': {'taxable_income': 1200000, 'tax': 187500},
            'new_regime': {'taxable_income': 1250000, 'tax': 175000}
        }
    }
    return render_template('results.html', **data)



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

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7860, debug=True)