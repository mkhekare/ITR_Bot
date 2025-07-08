from flask import Flask, request, render_template
from services.document_analysis import analyze_document
from services.tax_insights import generate_tax_insights

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    insights = None
    if request.method == 'POST':
        uploaded_file = request.files['document']
        if uploaded_file:
            document_text = analyze_document(uploaded_file)
            insights = generate_tax_insights(document_text)
    return render_template('index.html', insights=insights)

if __name__ == '__main__':
    app.run(debug=True)