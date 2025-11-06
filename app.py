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
import easyocr
import os
from io import BytesIO

app = Flask(__name__)
CORS(app)

# Khởi tạo EasyOCR (chỉ chạy 1 lần)
reader = easyocr.Reader(['en', 'vi'], gpu=False)

# Hàm dịch văn bản bằng deep-translator
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
    
    # Đọc ảnh
    filestr = file.read()
    npimg = np.frombuffer(filestr, np.uint8)
    img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
    
    # OCR
    result = reader.readtext(img, detail=0, paragraph=True)
    ocr_text = "\n".join(result)
    
    # Dịch
    translated = translate_text(ocr_text, target_lang)
    
    return jsonify({
        "original": ocr_text,
        "translated": translated
    })

# === 2. DỊCH FILE WORD (.	docx) ===
@app.route('/translate-docx', methods=['POST'])
def translate_docx():
    if 'file' not in request.files:
        return jsonify({"error": "Không có file"}), 400
    
    file = request.files['file']
    target_lang = request.form.get('lang', 'vi')
    
    doc = Document(file)
    full_text = []
    for para in doc.paragraphs:
        if para.text.strip():
            full_text.append(para.text)
    
    original = "\n".join(full_text)
    translated = translate_text(original, target_lang)
    
    return jsonify({
        "original": original,
        "translated": translated
    })

# === 3. DỊCH FILE POWERPOINT (.pptx) ===
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
            if hasattr(shape, "text"):
                if shape.text.strip():
                    full_text.append(shape.text)
    
    original = "\n".join(full_text)
    translated = translate_text(original, target_lang)
    
    return jsonify({
        "original": original,
        "translated": translated
    })

# === 4. DỊCH FILE PDF ===
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
    
    return jsonify({
        "original": full_text,
        "translated": translated
    })

# === 5. DỊCH VĂN BẢN THƯỜNG ===
@app.route('/translate-text', methods=['POST'])
def translate_text_endpoint():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({"error": "Không có văn bản"}), 400
    
    text = data['text']
    target_lang = data.get('lang', 'vi')
    
    translated = translate_text(text, target_lang)
    
    return jsonify({
        "original": text,
        "translated": translated
    })

# === 6. XUẤT FILE PDF ĐÃ DỊCH ===
@app.route('/export-pdf', methods=['POST'])
def export_pdf():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({"error": "Không có văn bản"}), 400
    
    text = data['text']
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Thêm văn bản (xử lý Unicode)
    for line in text.split('\n'):
        pdf.cell(200, 10, txt=line.encode('latin-1', 'replace').decode('latin-1'), ln=1)
    
    output = BytesIO()
    pdf.output(output)
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/pdf',
        as_attachment=True,
        download_name='translated.pdf'
    )

# === TRANG CHỦ ===
@app.route('/')
def home():
    return """
    <h1>Dịch Ảnh Của Tôi - API</h1>
    <p>Các endpoint:</p>
    <ul>
        <li>POST /translate-image (file + lang)</li>
        <li>POST /translate-docx</li>
        <li>POST /translate-pptx</li>
        <li>POST /translate-pdf</li>
        <li>POST /translate-text (JSON: {"text": "...", "lang": "vi"})</li>
        <li>POST /export-pdf (JSON: {"text": "..."})</li>
    </ul>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
