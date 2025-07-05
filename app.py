from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os
import logging
from utils.document_processor import process_uploaded_file
from utils.tax_calculator import calculate_tax

# Initialize Flask app
app = Flask(__name__)

# Basic configuration
app.config['SECRET_KEY'] = 'dev-secret-key'
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'txt'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    # Dummy data for dashboard
    dummy_data = {
        'tax_liability': 45200,
        'gst_returns': 12450,
        'portfolio_value': 485000,
        'recent_activity': [
            {'title': 'Salary slip processed', 'amount': 85000, 'status': 'completed'},
            {'title': 'GSTR-3B Due', 'due_date': '2024-08-20', 'status': 'pending'}
        ]
    }
    return render_template('dashboard.html', data=dummy_data)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'files' not in request.files:
            flash('No files selected', 'danger')
            return redirect(request.url)
        
        files = request.files.getlist('files')
        if not files or files[0].filename == '':
            flash('No files selected', 'danger')
            return redirect(request.url)
        
        try:
            financial_year = request.form.get('financial_year', '2025-26')
            age_group = request.form.get('age_group', 'below_60')
            
            extracted_data = {
                'salary_components': {},
                'other_income': {},
                'deductions': {},
                'documents': []
            }
            
            for file in files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    
                    result = process_uploaded_file(filepath)
                    extracted_data['documents'].append({
                        'filename': filename,
                        'summary': result.get('summary', 'Analysis completed')
                    })
                    
                    # Merge extracted data
                    for key in ['salary_components', 'other_income', 'deductions']:
                        if key in result:
                            extracted_data[key].update(result[key])
            
            # Calculate tax
            tax_results = calculate_tax(
                salary_components=extracted_data['salary_components'],
                other_income=extracted_data['other_income'],
                deductions=extracted_data['deductions'],
                age_group=age_group,
                financial_year=financial_year
            )
            
            return render_template('results.html',
                                extracted_data=extracted_data,
                                tax_results=tax_results)
        
        except Exception as e:
            logger.error(f"Error processing documents: {str(e)}")
            flash('Error analyzing documents. Please try again.', 'danger')
            return redirect(request.url)
    
    return render_template('upload.html')

@app.route('/calculator')
def calculator():
    return render_template('calculator.html')

@app.route('/gst')
def gst():
    return render_template('gst.html')

@app.route('/investments')
def investments():
    return render_template('investments.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Server Error: {error}")
    return render_template('errors/500.html'), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)