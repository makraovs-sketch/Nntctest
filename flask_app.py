import os
import requests
import pdfplumber
import io
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

def get_pdf_text():
    # Твоя ссылка на PDF (НРТК)
    url = "https://cloud.nntc.nnov.ru/index.php/s/fYpXD39YccFB5gM/download"
    response = requests.get(url, timeout=20)
    with pdfplumber.open(io.BytesIO(response.content)) as pdf:
        return "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])

@app.route('/get_schedule', methods=['GET'])
def get_schedule():
    target_group = request.args.get('group')
    api_key = os.environ.get("GEMINI_API_KEY")
    
    try:
        pdf_text = get_pdf_text()
        
        # Прямой запрос к Google API без посредников
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"Извлеки расписание всех групп в JSON. Формат: {{'Группа': [{{'para_num': '1', 'subject': 'Урок', 'teacher': 'ФИО', 'aud': '101', 'time': '8:30'}}]}}. Текст: {pdf_text}"
                }]
            }]
        }
        
        headers = {'Content-Type': 'application/json'}
        response = requests.post(api_url, json=payload, headers=headers)
        res_data = response.json()
        
        # Вытаскиваем текст из ответа Google
        raw_text = res_data['candidates'][0]['content']['parts'][0]['text']
        
        # Чистим JSON от лишних символов
        clean_json = raw_text.strip()
        if "```json" in clean_json:
            clean_json = clean_json.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_json:
            clean_json = clean_json.split("```")[1].split("```")[0].strip()
            
        full_schedule = json.loads(clean_json)
        
        if target_group:
            return jsonify({target_group: full_schedule.get(target_group, [])})
        return jsonify(full_schedule)

    except Exception as e:
        return jsonify({"error": "Ошибка прямого запроса", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

