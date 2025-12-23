
import os
import requests
import pdfplumber
import io
from flask import Flask, request, jsonify
from google import genai
from google.genai import types

app = Flask(__name__)

# Настройка клиента Gemini (ключ возьмем из настроек сервера)
client = genai.Client(
    api_key=os.environ.get("GEMINI_API_KEY"),
)

SYSTEM_INSTRUCTION = """Ты — парсер расписания. Тебе будут давать текст из PDF-файла. Твоя задача — найти в нем замены для групп.
Результат выдавай СТРОГО в формате JSON.
Формат: {"НазваниеГруппы": [{"para_num": "номер", "subject": "предмет (дата)", "teacher": "фамилия", "aud": "кабинет", "time": "время"}]}.
Если данных нет — возвращай пустой список []. Не пиши ничего, кроме JSON."""

def get_pdf_text():
    # Ссылка на твой PDF (всегда свежий)
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
    
    try:
        # 1. Получаем текст из PDF
        pdf_text = get_pdf_text()
        
        # 2. Отправляем в Gemini (как ты делал в AI Studio)
        response = client.models.generate_content(
            model="gemini-2.0-flash", # Или та версия, которая была в AI Studio
            contents=[pdf_text],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.1 # Ставим низкую, чтобы ИИ не фантазировал
            )
        )
        
        # 3. Превращаем текст ответа в настоящий JSON
        import json
        full_schedule = json.loads(response.text.replace('```json', '').replace('```', ''))
        
        # 4. Если пользователь просил конкретную группу - отдаем её, иначе всё сразу
        if target_group:
            group_data = full_schedule.get(target_group, [])
            return jsonify({target_group: group_data})
        
        return jsonify(full_schedule)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
