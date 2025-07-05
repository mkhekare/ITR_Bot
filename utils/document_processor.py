import os
import re
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import google.generativeai as genai
from config import Config

def extract_text_from_file(filepath):
    """Robust text extraction with error handling"""
    try:
        if filepath.lower().endswith('.pdf'):
            with open(filepath, 'rb') as f:
                images = convert_from_bytes(f.read())
            text = ""
            for img in images:
                text += pytesseract.image_to_string(img)
            return text
        
        elif filepath.lower().endswith(('.png', '.jpg', '.jpeg')):
            return pytesseract.image_to_string(Image.open(filepath))
        
        elif filepath.lower().endswith('.txt'):
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
                
        return ""
    except Exception as e:
        print(f"Error extracting text from {filepath}: {str(e)}")
        return ""

def analyze_financial_content(content):
    """Enhanced financial data extraction"""
    result = {
        'salary_components': {},
        'other_income': {},
        'deductions': {},
        'summary': "Analysis completed"
    }
    
    # Salary components regex
    salary_patterns = {
        'basic': r'(basic\s*salary|basic)[^\d]*(\d[\d,]*)',
        'hra': r'(house\s*rent|hra)[^\d]*(\d[\d,]*)',
        'bonus': r'(bonus|incentive)[^\d]*(\d[\d,]*)'
    }
    
    # Deductions regex
    deduction_patterns = {
        '80c': r'(section\s*80c|80c|ppf|lic)[^\d]*(\d[\d,]*)',
        '80d': r'(section\s*80d|80d|medical\s*insurance)[^\d]*(\d[\d,]*)',
        'hla': r'(home\s*loan|housing\s*loan|hla)[^\d]*(\d[\d,]*)'
    }
    
    # Extract salary components
    for key, pattern in salary_patterns.items():
        matches = re.finditer(pattern, content.lower())
        for match in matches:
            try:
                amount = float(match.group(2).replace(',', ''))
                result['salary_components'][key] = result['salary_components'].get(key, 0) + amount
            except:
                continue
    
    # Extract deductions
    for key, pattern in deduction_patterns.items():
        matches = re.finditer(pattern, content.lower())
        for match in matches:
            try:
                amount = float(match.group(2).replace(',', ''))
                result['deductions'][key] = result['deductions'].get(key, 0) + amount
            except:
                continue
    
    return result

def process_uploaded_file(filepath):
    """Main processing function with fallback mechanisms"""
    try:
        content = extract_text_from_file(filepath)
        if not content:
            return {'summary': 'Could not extract text from document'}
        
        # First try AI analysis
        try:
            genai.configure(api_key=Config.GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-pro')
            
            prompt = f"""Extract financial data from this document:
            - Salary components (basic, HRA, allowances)
            - Deductions (80C, 80D, home loan)
            - Other income
            
            Return JSON format with amounts as numbers.
            Document content: {content[:10000]}"""
            
            response = model.generate_content(prompt)
            return eval(response.text)
            
        except Exception as ai_error:
            print(f"AI analysis failed, using regex fallback: {ai_error}")
            return analyze_financial_content(content)
            
    except Exception as e:
        print(f"Error processing file {filepath}: {str(e)}")
        return {'summary': f'Error processing document: {str(e)}'}