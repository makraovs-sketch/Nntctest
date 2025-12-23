import os
import requests
import pdfplumber
import io
import google.generativeai as genai
from flask import Flask, jsonify, request

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# Вставь сюда свой скопированный ключ из AI Studio
genai.configure(api_key="AIzaSyBa0z34RJTWZaX5u84J2ElQM_uAsfcEMfY")
model = genai.GenerativeModel('gemini-1.5-flash')

PDF_URL = "https://cloud.nntc.nnov.ru/index.php/s/fYpXD39YccFB5gM/download"

@app.route('/get_schedule')
def get_schedule():
    group = request.args.get('group', '1ИСИП-25-3к')
    try:
        response = requests.get(PDF_URL, timeout=15)
        raw_text = ""
        
        # Вытаскиваем весь текст из PDF
        with pdfplumber.open(io.BytesIO(response.content)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    raw_text += page_text + "\n"

        # Промпт для Gemini: просим найти данные и вернуть JSON
        prompt = f"""
        Найди в этом тексте замены для учебной группы {group}. 
        Верни результат ТОЛЬКО в формате JSON списка объектов. 
        Поля: "para_num" (номер пары), "subject" (предмет), "teacher" (преподаватель), "aud" (кабинет), "time" (время).
        Если замен нет, верни пустой список [].
        Текст расписания:
        {raw_text}
        """

        ai_response = model.generate_content(prompt)
        
        # Убираем лишние символы из ответа AI
        clean_json = ai_response.text.replace('```json', '').replace('```', '').strip()
        
        return clean_json
    except Exception as e:
        return jsonify([{"subject": f"Ошибка сервера: {str(e)}"}])

if __name__ == '__main__':
    app.run()
