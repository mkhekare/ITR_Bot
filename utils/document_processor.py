import os
import re
from PIL import Image
import pytesseract
from pdf2image import convert_from_bytes
import magic
import google.generativeai as genai

def extract_text_from_image(image_path):
    """Extract text from image using OCR"""
    try:
        if image_path.lower().endswith('.pdf'):
            images = convert_from_bytes(open(image_path, 'rb').read())
            text = ""
            for img in images:
                text += pytesseract.image_to_string(img)
            return text
        else:
            return pytesseract.image_to_string(Image.open(image_path))
    except Exception as e:
        print(f"Error in OCR: {e}")
        return ""

def analyze_with_gemini(content, doc_type, model):
    """Analyze document content with Gemini"""
    try:
        prompt = f"""Analyze this {doc_type} document for income tax filing purposes. Extract:
        1. Salary components (basic, HRA, allowances, bonuses)
        2. Other income (interest, capital gains, rental income)
        3. Eligible deductions (80C, 80D, etc.)
        4. Any other tax-relevant information
        
        Return in JSON format with these keys: salary_components, other_income, deductions, summary.
        For amounts, always convert to annual figures if not already.
        Document content: {content[:15000]}"""  # Limit content to avoid context overflow
        
        response = model.generate_content(prompt)
        
        # Simple parsing of Gemini response (would need more robust parsing in production)
        try:
            # Try to find JSON in the response
            json_str = re.search(r'\{.*\}', response.text, re.DOTALL).group()
            return eval(json_str)
        except:
            # Fallback to extracting key information with regex if JSON parsing fails
            result = {
                'salary_components': {},
                'other_income': {},
                'deductions': {},
                'summary': response.text
            }
            
            # Extract salary components
            salary_matches = re.finditer(r'(basic|hra|allowance|bonus|special allowance)[^\d]*(\d[\d,]+)', content.lower())
            for match in salary_matches:
                component = match.group(1)
                amount = float(match.group(2).replace(',', ''))
                result['salary_components'][component] = amount
            
            # Extract deductions
            ded_matches = re.finditer(r'(section\s*80[cdefg]|ppf|lic|elss|nps|medical insurance)[^\d]*(\d[\d,]+)', content.lower())
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

def process_uploaded_file(filepath, model):
    """Process an uploaded file and extract tax-relevant information"""
    mime = magic.Magic()
    file_type = mime.from_file(filepath)
    
    # Extract text based on file type
    if 'text' in file_type.lower() or filepath.lower().endswith('.txt'):
        with open(filepath, 'r') as f:
            content = f.read()
    elif 'pdf' in file_type.lower() or filepath.lower().endswith('.pdf'):
        content = extract_text_from_image(filepath)
    elif 'image' in file_type.lower() or any(filepath.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg']):
        content = extract_text_from_image(filepath)
    else:
        content = f"Unsupported file type: {file_type}"
    
    # Determine document type for better analysis
    doc_type = "financial document"
    if 'salary' in filepath.lower() or 'payslip' in filepath.lower():
        doc_type = "salary slip"
    elif 'form 16' in filepath.lower():
        doc_type = "Form 16"
    elif 'receipt' in filepath.lower() or 'bill' in filepath.lower():
        doc_type = "receipt/bill"
    elif 'statement' in filepath.lower() or 'portfolio' in filepath.lower():
        doc_type = "investment statement"
    
    # Analyze with Gemini
    analysis_result = analyze_with_gemini(content, doc_type, model)
    analysis_result['content'] = content[:1000] + "..." if len(content) > 1000 else content  # Store truncated content
    
    return analysis_result