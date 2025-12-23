
from flask import Flask, jsonify, request
import pdfplumber
import requests
import io

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False 

PDF_URL = "https://cloud.nntc.nnov.ru/index.php/s/fYpXD39YccFB5gM/download"

@app.route('/get_schedule')
def get_schedule():
    group_target = request.args.get('group', '').strip()
    if not group_target:
        return jsonify([])

    try:
        response = requests.get(PDF_URL, timeout=15)
        with pdfplumber.open(io.BytesIO(response.content)) as pdf:
            schedule = []
            for page in pdf.pages:
                table = page.extract_table()
                if not table: continue
                
                for row in table:
                    # Чистим ячейки
                    r = [str(c).replace('\n', ' ').strip() if c else "" for c in row]
                    
                    # Ищем строку с твоей группой
                    if group_target.lower() in " ".join(r).lower():
                        # Пытаемся вытащить данные по порядку
                        schedule.append({
                            "group": group_target,
                            "para_num": r[2] if len(r) > 2 else "?",       # Номер пары (1, 2, 3...)
                            "subject": r[1] if len(r) > 1 else "Замена",   # Предмет
                            "teacher": r[3] if len(r) > 3 else "—",         # Преподаватель
                            "aud": r[5] if len(r) > 5 and r[5] else "—",    # Кабинет
                            "time": r[4] if len(r) > 4 and r[4] else "—"    # Время
                        })
            
            # Если по группе пусто
            if not schedule:
                return jsonify([{"subject": "Замен не найдено", "group": group_target, "para_num": "-"}])
                
            return jsonify(schedule)
            
    except Exception as e:
        return jsonify([{"subject": "Ошибка доступа к PDF", "para_num": "!"}])

if __name__ == '__main__':
    app.run()
