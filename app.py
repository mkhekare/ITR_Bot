from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from utils.document_processor import process_uploaded_file
import os
from config import Config
from datetime import datetime
import google.generativeai as genai

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Initialize Gemini
genai.configure(api_key=app.config['GEMINI_API_KEY'])
model = genai.GenerativeModel('gemini-1.5-flash')

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    tax_profiles = db.relationship('TaxProfile', backref='user', lazy=True)
    gst_profiles = db.relationship('GSTProfile', backref='user', lazy=True)

class TaxProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    pan_number = db.Column(db.String(10))
    financial_year = db.Column(db.String(9))
    regime = db.Column(db.String(20))
    # Add other tax-related fields

class GSTProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    gstin = db.Column(db.String(15))
    business_name = db.Column(db.String(100))
    # Add other GST-related fields

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'txt'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# app.py
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/calculator')
def calculator():
    return render_template('calculator.html')  # Not calculator/step1.html

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # Handle file upload
        pass
    return render_template('upload.html')

@app.route('/results')
def results():
    return render_template('results.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')

# Add these routes to your existing app.py
@app.route('/gst')
def gst():
    return render_template('gst.html')

@app.route('/investments')
def investments():
    return render_template('investments.html')

@app.route('/resources')
def resources():
    return render_template('advisory/resources.html')

@app.route('/blog')
def blog():
    return render_template('blog.html')

@app.route('/advisory')
def advisory():
    return render_template('advisory.html')

# GST Routes
@app.route('/gst')
@login_required
def gst_dashboard():
    return render_template('gst/dashboard.html')

# Investments Routes
@app.route('/investments')
@login_required
def investments_dashboard():
    return render_template('investments/dashboard.html')

# Business Solutions Routes
@app.route('/business')
@login_required
def business_dashboard():
    return render_template('business/dashboard.html')

# Advisory Routes
@app.route('/advisory')
def advisory_resources():
    return render_template('advisory/resources.html')

# Auth Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'danger')
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
        else:
            user = User(
                email=email,
                name=name,
                password_hash=generate_password_hash(password)
            )
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for('dashboard'))
    return render_template('auth/register.html')

@app.route('/analyze', methods=['POST'])
def analyze_documents():
    if 'files' not in request.files:
        flash('No files uploaded', 'danger')
        return redirect(url_for('upload'))
    
    files = request.files.getlist('files')
    financial_year = request.form.get('financial_year')
    age_group = request.form.get('age_group')
    
    extracted_data = {
        'salary_components': {},
        'other_income': {},
        'deductions': {},
        'documents': []
    }
    
    for file in files:
        if file.filename == '':
            continue
            
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Process each file
            result = process_uploaded_file(filepath)
            extracted_data['documents'].append({
                'filename': filename,
                'content': result['content'][:1000] + "..." if len(result['content']) > 1000 else result['content'],
                'summary': result['summary']
            })
            
            # Aggregate data
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
    
    return render_template('results.html', 
                         extracted_data=extracted_data,
                         tax_results=tax_results)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# AI Assistant Endpoint
@app.route('/ask_gemini', methods=['POST'])
def ask_gemini():
    user_question = request.form.get('question')
    context = request.form.get('context', '')
    
    prompt = f"""As a professional tax advisor, provide accurate and helpful information about:
    {context}
    Question: {user_question}
    
    Answer concisely with relevant tax sections when applicable."""
    
    response = model.generate_content(prompt)
    return response.text

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)