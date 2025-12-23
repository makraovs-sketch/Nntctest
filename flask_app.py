import os
import requests
import pdfplumber
import io
import json
import time
from flask import Flask, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# --- НАСТРОЙКИ ---
CACHE_FILE = "schedule_cache.json"
CACHE_TIME = 3600 

# Настройка API
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# Стабильный вызов модели
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction="Ты — парсер расписания. Выдавай СТРОГО JSON. Формат: {'Группа': [{'para_num': '1', 'subject': 'Математика', 'teacher': 'Иванов', 'aud': '101', 'time': '8:30'}]}"
)

def get_pdf_text():
    url = "https://cloud.nntc.nnov.ru/index.php/s/fYpXD39YccFB5gM/download"
    response = requests.get(url, timeout=15)
    with pdfplumber.open(io.BytesIO(response.content)) as pdf:
        return "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])

@app.route('/get_schedule', methods=['GET'])
def get_schedule():
    target_group = request.args.get('group')
    
    # 1. Кэш
    if os.path.exists(CACHE_FILE):
        if (time.time() - os.path.getmtime(CACHE_FILE)) < CACHE_TIME:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return jsonify({target_group: data.get(target_group, [])} if target_group else data)

    # 2. Запрос к ИИ
    try:
        text = get_pdf_text()
        response = model.generate_content(text)
        
        # Чистим JSON
        clean_json = response.text.strip()
        if "```json" in clean_json:
            clean_json = clean_json.split("```json")[1].split("```")[0].strip()
        
        full_schedule = json.loads(clean_json)
        
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(full_schedule, f, ensure_ascii=False)
            
        return jsonify({target_group: full_schedule.get(target_group, [])} if target_group else full_schedule)

    except Exception as e:
        return jsonify({"error": str(e), "hint": "Check API key or Model name"}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

