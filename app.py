import os
import io
import magic
import numpy as np
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image
from pdf2image import convert_from_bytes
import pytesseract
from utils.document_processor import process_uploaded_file, extract_text_from_image
from utils.tax_calculator import calculate_tax, get_tax_saving_tips

# Load environment variables
load_dotenv()

# Configure Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'txt'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_files():
    if request.method == 'POST':
        # Get form data
        age_group = request.form.get('age_group')
        financial_year = request.form.get('financial_year')
        
        # Initialize data structure
        extracted_data = {
            'salary_components': {},
            'other_income': {},
            'deductions': {},
            'documents': []
        }
        
        # Process uploaded files
        if 'files' not in request.files:
            flash('No files uploaded')
            return redirect(request.url)
        
        files = request.files.getlist('files')
        for file in files:
            if file.filename == '':
                continue
                
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                # Process each file
                result = process_uploaded_file(filepath, model)
                extracted_data['documents'].append({
                    'filename': filename,
                    'content': result['content'],
                    'summary': result['summary']
                })
                
                # Update extracted data
                if 'salary_components' in result:
                    extracted_data['salary_components'].update(result['salary_components'])
                if 'other_income' in result:
                    extracted_data['other_income'].update(result['other_income'])
                if 'deductions' in result:
                    extracted_data['deductions'].update(result['deductions'])
        
        # Calculate tax
        tax_results = calculate_tax(
            salary_components=extracted_data['salary_components'],
            other_income=extracted_data['other_income'],
            deductions=extracted_data['deductions'],
            age_group=age_group,
            financial_year=financial_year
        )
        
        # Get optimization tips
        optimization_tips = get_tax_saving_tips(
            current_deductions=extracted_data['deductions'],
            income=sum(extracted_data['salary_components'].values()) + sum(extracted_data['other_income'].values()),
            age_group=age_group,
            model=model
        )
        
        return render_template('results.html', 
                            extracted_data=extracted_data,
                            tax_results=tax_results,
                            optimization_tips=optimization_tips)
    
    return render_template('upload.html')

@app.route('/faq')
def faq():
    # Generate FAQ content using Gemini
    prompt = """Generate a comprehensive FAQ section for an Indian income tax filing assistant. 
    Include questions about:
    1. Difference between old and new tax regimes
    2. Common deductions available
    3. Documents required for filing
    4. How to claim HRA exemption
    5. Tax benefits on home loans
    6. Capital gains tax on equity investments
    7. Last minute tax saving options
    8. How to claim refunds
    
    Format the response in HTML with questions in <h3> tags and answers in <p> tags."""
    
    response = model.generate_content(prompt)
    faq_content = response.text
    
    return render_template('faq.html', faq_content=faq_content)

@app.route('/ask_gemini', methods=['POST'])
def ask_gemini():
    user_question = request.form.get('question')
    context = request.form.get('context', '')
    
    prompt = f"""You are a helpful AI tax assistant for Indian income tax filing. 
    Context: {context}
    Question: {user_question}
    
    Provide a clear, concise answer with relevant sections of the Income Tax Act when applicable."""
    
    response = model.generate_content(prompt)
    return response.text

if __name__ == '__main__':
    app.run(debug=True)