import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import re
import google.generativeai as genai

def extract_text_from_file(filepath):
    """Extract text from various file formats"""
    try:
        if filepath.lower().endswith('.pdf'):
            images = convert_from_path(filepath)
            text = ""
            for img in images:
                text += pytesseract.image_to_string(img)
            return text
        elif filepath.lower().endswith(('.png', '.jpg', '.jpeg')):
            return pytesseract.image_to_string(Image.open(filepath))
        elif filepath.lower().endswith('.txt'):
            with open(filepath, 'r') as f:
                return f.read()
        return ""
    except Exception as e:
        print(f"Error extracting text: {e}")
        return ""

def analyze_with_gemini(content, doc_type):
    """Analyze document content with Gemini AI"""
    try:
        prompt = f"""Analyze this {doc_type} document for tax filing. Extract:
        1. Salary components (basic, HRA, allowances, bonuses)
        2. Other income (interest, capital gains, rental income)
        3. Eligible deductions (80C, 80D, etc.)
        
        Return JSON with these keys: salary_components, other_income, deductions, summary.
        For amounts, convert to annual figures if not already.
        
        Document content: {content[:15000]}"""
        
        response = genai.generate_content(prompt)
        
        try:
            # Try to parse JSON response
            import json
            return json.loads(response.text)
        except:
            # Fallback to regex extraction
            result = {
                'salary_components': {},
                'other_income': {},
                'deductions': {},
                'summary': response.text
            }
            
            # Extract salary components
            salary_matches = re.finditer(r'(basic|hra|allowance|bonus)[^\d]*(\d[\d,]+)', content.lower())
            for match in salary_matches:
                component = match.group(1)
                amount = float(match.group(2).replace(',', ''))
                result['salary_components'][component] = amount
            
            # Extract deductions
            ded_matches = re.finditer(r'(section\s*80[cdefg]|ppf|lic|elss|nps)[^\d]*(\d[\d,]+)', content.lower())
            for match in ded_matches:
                component = match.group(1)
                amount = float(match.group(2).replace(',', ''))
                result['deductions'][component] = amount
                
            return result
            
    except Exception as e:
        print(f"Error analyzing with Gemini: {e}")
        return {
            'salary_components': {},
            'other_income': {},
            'deductions': {},
            'summary': f"Analysis failed: {str(e)}"
        }

def process_uploaded_file(filepath):
    """Process an uploaded file and extract tax-relevant information"""
    content = extract_text_from_file(filepath)
    
    # Determine document type
    doc_type = "financial document"
    if 'salary' in filepath.lower() or 'payslip' in filepath.lower():
        doc_type = "salary slip"
    elif 'form 16' in filepath.lower():
        doc_type = "Form 16"
    elif 'receipt' in filepath.lower() or 'bill' in filepath.lower():
        doc_type = "receipt/bill"
    
    # Analyze with Gemini
    return analyze_with_gemini(content, doc_type)