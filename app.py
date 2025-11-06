# app.py
import cv2
import numpy as np
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from deep_translator import GoogleTranslator
from docx import Document
from pptx import Presentation
import pdfplumber
from fpdf import FPDF
import pytesseract
import os
from io import BytesIO

# Cấu hình Tesseract (Render có sẵn)
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

app = Flask(__name__)
CORS(app)

# Hàm dịch
def translate_text(text, target='vi'):
    if not text.strip():
        return text
    try:
        return GoogleTranslator(source='auto', target=target).translate(text)
    except Exception as e:
        print(f"Lỗi dịch: {e}")
        return text

# === 1. DỊCH ẢNH ===
@app.route('/translate-image', methods=['POST'])
def translate_image():
    if 'file' not in request.files:
        return jsonify({"error": "Không có file"}), 400
    
    file = request.files['file']
    target_lang = request.form.get('lang', 'vi')
    
    filestr = file.read()
    npimg = np.frombuffer(filestr, np.uint8)
    img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
    
    # Dùng pytesseract
    custom_config = r'--oem 3 --psm 6'
    ocr_text = pytesseract.image_to_string(img, lang='eng+vie', config=custom_config)
    
    translated = translate_text(ocr_text, target_lang)
    
    return jsonify({
        "original": ocr_text,
        "translated": translated
    })

# === CÁC HÀM KHÁC GIỮ NGUYÊN ===
@app.route('/translate-docx', methods=['POST'])
def translate_docx():
    if 'file' not in request.files:
        return jsonify({"error": "Không có file"}), 400
    file = request.files['file']
    target_lang = request.form.get('lang', 'vi')
    doc = Document(file)
    full_text = [para.text for para in doc.paragraphs if para.text.strip()]
    original = "\n".join(full_text)
    translated = translate_text(original, target_lang)
    return jsonify({"original": original, "translated": translated})

@app.route('/translate-pptx', methods=['POST'])
def translate_pptx():
    if 'file' not in request.files:
        return jsonify({"error": "Không có file"}), 400
    file = request.files['file']
    target_lang = request.form.get('lang', 'vi')
    prs = Presentation(file)
    full_text = []
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text.strip():
                full_text.append(shape.text)
    original = "\n".join(full_text)
    translated = translate_text(original, target_lang)
    return jsonify({"original": original, "translated": translated})

@app.route('/translate-pdf', methods=['POST'])
def translate_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "Không có file"}), 400
    file = request.files['file']
    target_lang = request.form.get('lang', 'vi')
    full_text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
    translated = translate_text(full_text, target_lang)
    return jsonify({"original": full_text, "translated": translated})

@app.route('/translate-text', methods=['POST'])
def translate_text_endpoint():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({"error": "Không có văn bản"}), 400
    text = data['text']
    target_lang = data.get('lang', 'vi')
    translated = translate_text(text, target_lang)
    return jsonify({"original": text, "translated": translated})

@app.route('/export-pdf', methods=['POST'])
def export_pdf():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({"error": "Không có văn bản"}), 400
    text = data['text']
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in text.split('\n'):
        pdf.cell(200, 10, txt=line.encode('latin-1', 'replace').decode('latin-1'), ln=1)
    output = BytesIO()
    pdf.output(output)
    output.seek(0)
    return send_file(output, mimetype='application/pdf', as_attachment=True, download_name='translated.pdf')

@app.route('/')
def home():
    return """
    <h1>Dịch Ảnh Của Tôi - API</h1>
    <p>Dùng pytesseract + deep-translator</p>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
