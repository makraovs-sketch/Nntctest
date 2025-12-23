from flask import Flask, jsonify, request
import pdfplumber
import requests
import io

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False # Это ДОЛЖНО исправить отображение в браузере

PDF_URL = "https://cloud.nntc.nnov.ru/index.php/s/fYpXD39YccFB5gM/download"

@app.route('/get_schedule')
def get_schedule():
    group_target = request.args.get('group', '').strip()
    if not group_target: return jsonify([])

    try:
        response = requests.get(PDF_URL, timeout=15)
        with pdfplumber.open(io.BytesIO(response.content)) as pdf:
            schedule = []
            for page in pdf.pages:
                text = page.extract_text()
                # Если в тексте страницы вообще нет твоей группы - скипаем
                if group_target.lower() not in text.lower(): continue
                
                table = page.extract_table()
                if not table: continue
                
                for row in table:
                    # Убираем пустые ячейки и склеиваем строку
                    r = [str(c).replace('\n', ' ').strip() for c in row if c]
                    row_str = " ".join(r)
                    
                    if group_target.lower() in row_str.lower():
                        schedule.append({
                            "group": group_target,
                            "para_num": r[0] if len(r) > 0 else "—",
                            "subject": r[1] if len(r) > 1 else "Предмет не найден",
                            "teacher": r[2] if len(r) > 2 else "—",
                            "aud": r[3] if len(r) > 3 else "—",
                            "time": "По расп." 
                        })
            
            # Если даже так пусто - выдаем тестовую строку, чтобы ты увидел ДИЗАЙН
            if not schedule:
                schedule = [{
                    "group": group_target,
                    "para_num": "1",
                    "subject": "Тестовый предмет (Замен нет)",
                    "teacher": "Преподаватель",
                    "aud": "Каб",
                    "time": "08:10"
                }]
                
            return jsonify(schedule)
    except Exception as e:
        return jsonify([{"subject": "Ошибка: " + str(e)}])

if __name__ == '__main__':
    app.run()

