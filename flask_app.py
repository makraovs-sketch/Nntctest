from flask import Flask, jsonify, request
import pdfplumber
import requests
import io

app = Flask(__name__)
# Эта строка заставляет сервер показывать русский текст красиво:
app.config['JSON_AS_ASCII'] = False 

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
                table = page.extract_table()
                if not table: continue
                for row in table:
                    r = [str(c).replace('\n', ' ').strip() if c else "" for c in row]
                    if group_target.lower() in " ".join(r).lower():
                        # Берем данные из колонок таблицы
                        schedule.append({
                            "group": group_target,
                            "para_num": r[2] if len(r) > 2 and r[2] else "—",
                            "subject": r[1] if len(r) > 1 and len(r[1]) > 5 else "Замена/Пара",
                            "teacher": r[3] if len(r) > 3 else "—",
                            "aud": r[5] if len(r) > 5 else (r[3] if "каб" in r[3].lower() else "—"),
                            "time": r[4] if len(r) > 4 else "—"
                        })
            return jsonify(schedule if schedule else [{"subject": "Замен не найдено"}])
    except:
        return jsonify([{"subject": "Ошибка сервера"}])

if __name__ == '__main__':
    app.run()

