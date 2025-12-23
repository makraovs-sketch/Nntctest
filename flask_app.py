import os
import requests
import pdfplumber
import io
import json
import time
from flask import Flask, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# Настройка API
# Обязательно добавьте GEMINI_API_KEY в Settings -> Environment на Render
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# Самое стабильное имя модели для текущего API
model = genai.GenerativeModel('gemini-1.5-flash')

def get_pdf_text():
    """Скачивает и читает PDF файл"""
    url = "https://cloud.nntc.nnov.ru/index.php/s/fYpXD39YccFB5gM/download"
    response = requests.get(url, timeout=15)
    with pdfplumber.open(io.BytesIO(response.content)) as pdf:
        return "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])

@app.route('/get_schedule', methods=['GET'])
def get_schedule():
    target_group = request.args.get('group')
    
    try:
        pdf_text = get_pdf_text()
        
        # Четкая инструкция для ИИ
        prompt = (
            "Действуй как парсер расписания. Прочитай текст и найди замены для групп. "
            "Выдай результат СТРОГО в формате JSON, где ключи - названия групп, "
            "а значения - списки объектов с полями: para_num, subject, teacher, aud, time. "
            f"Текст для анализа:\n{pdf_text}"
        )
        
        response = model.generate_content(prompt)
        
        # Очистка ответа от лишних знаков
        text_response = response.text.strip()
        if "```json" in text_response:
            text_response = text_response.split("```json")[1].split("```")[0].strip()
        elif "```" in text_response:
            text_response = text_response.split("```")[1].split("```")[0].strip()
            
        full_schedule = json.loads(text_response)
        
        # Если группа указана - возвращаем только её, если нет - всё расписание
        if target_group:
            return jsonify({target_group: full_schedule.get(target_group, [])})
        
        return jsonify(full_schedule)

    except Exception as e:
        return jsonify({"error": str(e), "hint": "Проверьте лимиты и ключ в AI Studio"}), 500

if __name__ == "__main__":
    # Запуск через встроенный сервер Flask для простоты
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

