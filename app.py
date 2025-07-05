from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
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

# Tax Calculator Routes
@app.route('/calculator', methods=['GET', 'POST'])
@login_required
def calculator():
    if request.method == 'POST':
        # Process calculator form data
        pass
    return render_template('calculator/step1.html')

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