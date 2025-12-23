import os
import requests
import pdfplumber
import io
import json
import time
from flask import Flask, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# Настройка API ключа из настроек Render
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# Самый стабильный способ выбора модели
model = genai.GenerativeModel('gemini-1.5-flash')

def get_pdf_text():
    url = "https://cloud.nntc.nnov.ru/index.php/s/fYpXD39YccFB5gM/download"
    response = requests.get(url, timeout=15)
    with pdfplumber.open(io.BytesIO(response.content)) as pdf:
        return "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])

@app.route('/get_schedule', methods=['GET'])
def get_schedule():
    target_group = request.args.get('group')
    
    try:
        pdf_text = get_pdf_text()
        
        # Инструкция прямо в запросе для надежности
        prompt = f"Извлеки расписание для всех групп из этого текста и верни СТРОГО JSON: {pdf_text}"
        
        response = model.generate_content(prompt)
        
        # Очистка JSON от кавычек маркдауна
        clean_json = response.text.strip()
        if "```json" in clean_json:
            clean_json = clean_json.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_json:
            clean_json = clean_json.split("```")[1].split("```")[0].strip()
            
        full_schedule = json.loads(clean_json)
        
        if target_group:
            return jsonify({target_group: full_schedule.get(target_group, [])})
        return jsonify(full_schedule)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

