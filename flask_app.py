import os
import requests
import pdfplumber
import io
import json
import time
from flask import Flask, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# Принудительная настройка API
API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)

# Явное указание модели без лишних префиксов
model = genai.GenerativeModel('gemini-1.5-flash')

def get_pdf_text():
    url = "https://cloud.nntc.nnov.ru/index.php/s/fYpXD39YccFB5gM/download"
    response = requests.get(url, timeout=20)
    with pdfplumber.open(io.BytesIO(response.content)) as pdf:
        text = ""
        for page in pdf.pages:
            content = page.extract_text()
            if content:
                text += content + "\n"
        return text

@app.route('/get_schedule', methods=['GET'])
def get_schedule():
    target_group = request.args.get('group')
    
    try:
        pdf_text = get_pdf_text()
        if not pdf_text.strip():
            return jsonify({"error": "PDF пустой или не читается"}), 400

        # Очень короткий промпт, чтобы не грузить лимиты
        prompt = f"Верни данные о заменах для групп из этого текста в формате JSON: {pdf_text}"
        
        # Попытка генерации с явным указанием модели
        response = model.generate_content(prompt)
        
        # Очистка JSON
        res_text = response.text.strip()
        if "```json" in res_text:
            res_text = res_text.split("```json")[1].split("```")[0].strip()
        elif "```" in res_text:
            res_text = res_text.split("```")[1].split("```")[0].strip()
            
        data = json.loads(res_text)
        
        if target_group:
            return jsonify({target_group: data.get(target_group, [])})
        return jsonify(data)

    except Exception as e:
        # Если снова 404, выведем список доступных моделей в лог
        return jsonify({
            "error": str(e),
            "note": "Если видите 404, проверьте регион API ключа в AI Studio"
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
import os
import requests
import pdfplumber
import io
import json
import time
from flask import Flask, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# Принудительная настройка API
API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)

# Явное указание модели без лишних префиксов
model = genai.GenerativeModel('gemini-1.5-flash')

def get_pdf_text():
    url = "https://cloud.nntc.nnov.ru/index.php/s/fYpXD39YccFB5gM/download"
    response = requests.get(url, timeout=20)
    with pdfplumber.open(io.BytesIO(response.content)) as pdf:
        text = ""
        for page in pdf.pages:
            content = page.extract_text()
            if content:
                text += content + "\n"
        return text

@app.route('/get_schedule', methods=['GET'])
def get_schedule():
    target_group = request.args.get('group')
    
    try:
        pdf_text = get_pdf_text()
        if not pdf_text.strip():
            return jsonify({"error": "PDF пустой или не читается"}), 400

        # Очень короткий промпт, чтобы не грузить лимиты
        prompt = f"Верни данные о заменах для групп из этого текста в формате JSON: {pdf_text}"
        
        # Попытка генерации с явным указанием модели
        response = model.generate_content(prompt)
        
        # Очистка JSON
        res_text = response.text.strip()
        if "```json" in res_text:
            res_text = res_text.split("```json")[1].split("```")[0].strip()
        elif "```" in res_text:
            res_text = res_text.split("```")[1].split("```")[0].strip()
            
        data = json.loads(res_text)
        
        if target_group:
            return jsonify({target_group: data.get(target_group, [])})
        return jsonify(data)

    except Exception as e:
        # Если снова 404, выведем список доступных моделей в лог
        return jsonify({
            "error": str(e),
            "note": "Если видите 404, проверьте регион API ключа в AI Studio"
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

