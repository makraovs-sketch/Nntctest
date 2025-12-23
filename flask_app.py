import os
import requests
import pdfplumber
import io
import json
import time
from flask import Flask, request, jsonify
from google import genai
from google.genai import types

app = Flask(__name__)

# --- НАСТРОЙКИ КЭША ---
CACHE_FILE = "schedule_cache.json"
CACHE_TIME = 3600  # Данные хранятся 1 час (в секундах)

# Настройка клиента Gemini
client = genai.Client(
    api_key=os.environ.get("GEMINI_API_KEY"),
)

SYSTEM_INSTRUCTION = """Ты — парсер расписания. Тебе будут давать текст из PDF-файла. Твоя задача — найти в нем замены для групп.
Результат выдавай СТРОГО в формате JSON.
Формат: {"НазваниеГруппы": [{"para_num": "номер", "subject": "предмет (дата)", "teacher": "фамилия", "aud": "кабинет", "time": "время"}]}.
Если данных нет — возвращай пустой список []. Не пиши ничего, кроме JSON."""

def get_pdf_text():
    url = "https://cloud.nntc.nnov.ru/index.php/s/fYpXD39YccFB5gM/download"
    response = requests.get(url)
    with pdfplumber.open(io.BytesIO(response.content)) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text()
    return text

@app.route('/get_schedule', methods=['GET'])
def get_schedule():
    target_group = request.args.get('group')
    
    # 1. Проверяем, есть ли свежий кэш в памяти сервера
    if os.path.exists(CACHE_FILE):
        file_age = time.time() - os.path.getmtime(CACHE_FILE)
        if file_age < CACHE_TIME:
            print("--- Берем данные из кэша (лимиты не тратим) ---")
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                full_schedule = json.load(f)
                if target_group:
                    return jsonify({target_group: full_schedule.get(target_group, [])})
                return jsonify(full_schedule)

    # 2. Если кэша нет или он старый (прошел час) — идем к Gemini
    try:
        print("--- Кэш устарел. Запрашиваем Gemini... ---")
        pdf_text = get_pdf_text()
        
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[pdf_text],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.1
            )
        )
        
        # Очищаем ответ от лишних символов (маркдаун ```json)
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        full_schedule = json.loads(clean_json)
        
        # Сохраняем результат в файл для кэширования
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(full_schedule, f, ensure_ascii=False)
            
        if target_group:
            return jsonify({target_group: full_schedule.get(target_group, [])})
        
        return jsonify(full_schedule)

    except Exception as e:
        return jsonify({"error": f"Ошибка сервера или лимитов: {str(e)}"}), 500

if __name__ == "__main__":
    # На Render порт задается через переменную окружения PORT
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
