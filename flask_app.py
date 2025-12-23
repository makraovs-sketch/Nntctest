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

# --- НАСТРОЙКИ ---
CACHE_FILE = "schedule_cache.json"
CACHE_TIME = 3600  # Кэш на 1 час

# Настройка клиента Gemini
client = genai.Client(
    api_key=os.environ.get("GEMINI_API_KEY"),
)

# Инструкция для ИИ, чтобы он видел ВСЕ группы
SYSTEM_INSTRUCTION = """Ты — профессиональный парсер расписания. 
Тебе дан текст из PDF-файла с заменами уроков. 
Твоя задача: извлечь замены для ВСЕХ групп, которые упоминаются в тексте.
Результат выдай СТРОГО в формате JSON.

Формат ответа:
{
  "Название Группы": [
    {
      "para_num": "номер пары",
      "subject": "название предмета и дата",
      "teacher": "фамилия преподавателя",
      "aud": "кабинет",
      "time": "время начала"
    }
  ]
}

Если для группы замен нет, не включай её в список. Если данных вообще нет, верни {}. 
Не пиши ничего, кроме чистого JSON."""

def get_pdf_text():
    url = "https://cloud.nntc.nnov.ru/index.php/s/fYpXD39YccFB5gM/download"
    response = requests.get(url)
    # Используем pdfplumber для качественного извлечения таблиц
    with pdfplumber.open(io.BytesIO(response.content)) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

@app.route('/get_schedule', methods=['GET'])
def get_schedule():
    target_group = request.args.get('group')
    
    # 1. Проверяем кэш (чтобы не тратить лимиты)
    if os.path.exists(CACHE_FILE):
        file_age = time.time() - os.path.getmtime(CACHE_FILE)
        if file_age < CACHE_TIME:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                full_schedule = json.load(f)
                if target_group:
                    return jsonify({target_group: full_schedule.get(target_group, [])})
                return jsonify(full_schedule)

    # 2. Если кэша нет или он старый — идем к Gemini 1.5 Flash
    try:
        pdf_text = get_pdf_text()
        
        response = client.models.generate_content(
            model="gemini-1.5-flash", 
            contents=[pdf_text],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.1
            )
        )
        
        # Очистка текста от лишних символов Markdown (```json ... ```)
        clean_json = response.text.strip()
        if "```json" in clean_json:
            clean_json = clean_json.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_json:
            clean_json = clean_json.split("```")[1].split("```")[0].strip()
            
        full_schedule = json.loads(clean_json)
        
        # Сохраняем в кэш
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(full_schedule, f, ensure_ascii=False)
            
        if target_group:
            return jsonify({target_group: full_schedule.get(target_group, [])})
        
        return jsonify(full_schedule)

    except Exception as e:
        return jsonify({"error": f"Ошибка: {str(e)}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
