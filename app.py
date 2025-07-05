from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from utils.document_processor import process_uploaded_file
from utils.tax_calculator import calculate_tax
import os
from config import Config
from datetime import datetime
import google.generativeai as genai

# Initialize Flask application
app = Flask(__name__)
app.config.from_object(Config)

# Database setup
db = SQLAlchemy(app)

# Authentication setup
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize Gemini AI
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
    # Add other tax-related fields as needed

class GSTProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    gstin = db.Column(db.String(15))
    business_name = db.Column(db.String(100))
    # Add other GST-related fields as needed

# Helper functions
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'txt'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/calculator')
@login_required
def calculator():
    return render_template('calculator.html')

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        if 'files' not in request.files:
            flash('No files selected', 'danger')
            return redirect(request.url)
        
        files = request.files.getlist('files')
        if not files or all(file.filename == '' for file in files):
            flash('No files selected', 'danger')
            return redirect(request.url)
            
        return redirect(url_for('analyze_documents'))
    
    return render_template('upload.html')

@app.route('/results')
@login_required
def results():
    # This should typically be accessed after document analysis
    return render_template('results.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')

# Feature-specific routes
@app.route('/gst')
@login_required
def gst_dashboard():
    return render_template('gst/dashboard.html')

@app.route('/investments')
@login_required
def investments_dashboard():
    return render_template('investments/dashboard.html')

@app.route('/business')
@login_required
def business_dashboard():
    return render_template('business/dashboard.html')

@app.route('/advisory')
@login_required
def advisory_resources():
    return render_template('advisory/resources.html')

@app.route('/blog')
def blog():
    return render_template('blog.html')

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        flash('Invalid email or password', 'danger')
    
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
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
            flash('Registration successful!', 'success')
            return redirect(url_for('dashboard'))
    
    return render_template('auth/register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Document processing and analysis
@app.route('/analyze', methods=['POST'])
@login_required
def analyze_documents():
    if 'files' not in request.files:
        flash('No files uploaded', 'danger')
        return redirect(url_for('upload'))
    
    files = request.files.getlist('files')
    financial_year = request.form.get('financial_year')
    age_group = request.form.get('age_group')
    
    if not files or all(file.filename == '' for file in files):
        flash('No files selected', 'danger')
        return redirect(url_for('upload'))
    
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
            
            try:
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
                    
            except Exception as e:
                app.logger.error(f"Error processing file {filename}: {str(e)}")
                flash(f'Error processing {filename}', 'danger')
                continue
    
    if not extracted_data['documents']:
        flash('No valid documents were processed', 'danger')
        return redirect(url_for('upload'))
    
    try:
        tax_results = calculate_tax(
            salary_components=extracted_data['salary_components'],
            other_income=extracted_data['other_income'],
            deductions=extracted_data['deductions'],
            age_group=age_group,
            financial_year=financial_year
        )
    except Exception as e:
        app.logger.error(f"Tax calculation error: {str(e)}")
        flash('Error calculating tax results', 'danger')
        return redirect(url_for('upload'))
    
    return render_template('results.html', 
                        extracted_data=extracted_data,
                        tax_results=tax_results)

# AI Assistant Endpoint
@app.route('/ask_gemini', methods=['POST'])
@login_required
def ask_gemini():
    user_question = request.form.get('question', '').strip()
    context = request.form.get('context', '').strip()
    
    if not user_question:
        return "Please provide a question", 400
    
    try:
        prompt = f"""As a professional tax advisor, provide accurate and helpful information about:
        {context}
        Question: {user_question}
        
        Answer concisely with relevant tax sections when applicable."""
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        app.logger.error(f"Gemini API error: {str(e)}")
        return "Sorry, there was an error processing your request", 500

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('errors/500.html'), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=app.config['DEBUG'])