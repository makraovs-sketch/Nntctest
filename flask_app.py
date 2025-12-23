from flask import Flask, jsonify, request
import pdfplumber
import requests
import io

app = Flask(__name__)
# Эта строка заставит браузер показывать русский текст нормально
app.config['JSON_AS_ASCII'] = False

PDF_URL = "https://cloud.nntc.nnov.ru/index.php/s/fYpXD39YccFB5gM/download"

@app.route('/')
def home():
    return "<h1>Сервер Tob11145 работает!</h1>"

@app.route('/get_schedule')
def get_schedule():
    group_target = request.args.get('group', '').strip()
    if not group_target:
        return jsonify([{"subject": "Укажите группу", "time": "ERR"}])

    try:
        # Пытаемся скачать файл
        response = requests.get(PDF_URL, timeout=15)

        with pdfplumber.open(io.BytesIO(response.content)) as pdf:
            schedule = []
            for page in pdf.pages:
                table = page.extract_table()
                if not table: continue
                for row in table:
                    row_content = [str(c).replace('\n', ' ').strip() if c else "" for c in row]
                    full_text = " ".join(row_content).lower()

                    if group_target.lower() in full_text:
                        schedule.append({
                            "time": row_content[4] if len(row_content) > 4 else "—",
                            "subject": row_content[1],
                            "para": f"Пара {row_content[2]}" if row_content[2] else "-",
                            "aud": row_content[3] if len(row_content) > 3 else "—"
                        })

            return jsonify(schedule if schedule else [{"subject": "Замен не найдено", "time": "ОК"}])

    except Exception as e:
        # Если сайт колледжа недоступен, выводим понятную ошибку
        return jsonify([{"subject": "Сайт колледжа недоступен", "time": "Error"}])

if __name__ == '__main__':
    app.run()
