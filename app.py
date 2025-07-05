from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from config import Config
from datetime import datetime
import google.generativeai as genai

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Database setup
db = SQLAlchemy(app)

# Authentication setup
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Initialize Gemini AI
genai.configure(api_key=app.config['GEMINI_API_KEY'])
model = genai.GenerativeModel('gemini-1.5-flash')

# Database Models
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

class GSTProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    gstin = db.Column(db.String(15))
    business_name = db.Column(db.String(100))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Helper Functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Main Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

# Document Handling Routes
@app.route('/upload', methods=['GET', 'POST'])
@login_required
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
@login_required
def calculator():
    if request.method == 'POST':
        # Process calculator form data
        return redirect(url_for('results'))
    return render_template('calculator.html')

@app.route('/results')
@login_required
def results():
    return render_template('results.html')

# GST Routes
@app.route('/gst')
@login_required
def gst():
    return render_template('gst.html')

# Investments Routes
@app.route('/investments')
@login_required
def investments():
    return render_template('investments.html')

# Information Routes
@app.route('/faq')
def faq():
    return render_template('faq.html')

@app.route('/advisory')
def advisory():
    return render_template('advisory/resources.html')

# Authentication Routes
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
            return redirect(url_for('dashboard'))
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
            return redirect(url_for('dashboard'))
    return render_template('auth/register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

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

# Initialize Database
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)