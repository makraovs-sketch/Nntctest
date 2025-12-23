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
CACHE_TIME = 3600  # Кэш на 1 час (3600 секунд)

# Инициализация клиента Gemini
# Обязательно добавь переменную GEMINI_API_KEY в Settings -> Environment на Render
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

SYSTEM_INSTRUCTION = """Ты — парсер расписания колледжа. 
Тебе дан текст из PDF. Твоя задача: найти данные о заменах для ВСЕХ групп.
Выдавай ответ СТРОГО в формате JSON.

Формат:
{
  "Название Группы": [
    {
      "para_num": "номер пары",
      "subject": "предмет и дата",
      "teacher": "фамилия",
      "aud": "кабинет",
      "time": "время"
    }
  ]
}

Если замен нет, верни {}. Не пиши ничего, кроме JSON."""

def get_pdf_text():
    """Скачивает PDF и извлекает текст"""
    url = "https://cloud.nntc.nnov.ru/index.php/s/fYpXD39YccFB5gM/download"
    response = requests.get(url, timeout=10)
    with pdfplumber.open(io.BytesIO(response.content)) as pdf:
        return "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])

@app.route('/get_schedule', methods=['GET'])
def get_schedule():
    target_group = request.args.get('group')
    
    # 1. Пробуем взять данные из кэша
    if os.path.exists(CACHE_FILE):
        file_age = time.time() - os.path.getmtime(CACHE_FILE)
        if file_age < CACHE_TIME:
            try:
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    full_schedule = json.load(f)
                    if target_group:
                        return jsonify({target_group: full_schedule.get(target_group, [])})
                    return jsonify(full_schedule)
            except:
                pass # Если файл битый, идем дальше к ИИ

    # 2. Запрос к ИИ
    try:
        pdf_text = get_pdf_text()
        
        # Используем проверенное имя модели
        response = client.models.generate_content(
            model="gemini-1.5-flash", 
            contents=pdf_text,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.1
            )
        )
        
        # Чистим ответ от лишнего (Markdown кавычек)
        raw_text = response.text.strip()
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0].strip()
            
        full_schedule = json.loads(raw_text)
        
        # Сохраняем в кэш для экономии лимитов
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(full_schedule, f, ensure_ascii=False)
            
        if target_group:
            return jsonify({target_group: full_schedule.get(target_group, [])})
        
        return jsonify(full_schedule)

    except Exception as e:
        return jsonify({
            "error": "Ошибка при обработке запроса",
            "details": str(e),
            "hint": "Проверьте API ключ и лимиты в Google AI Studio"
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
