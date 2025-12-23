
from flask import Flask, jsonify, request
import pdfplumber
import requests
import io

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False # Чтобы в браузере был русский текст, а не коды

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
                    # Чистим строку от пустых ячеек и переносов
                    r = [str(c).replace('\n', ' ').strip() if c else "" for c in row]
                    # Ищем группу (обычно она в 0 или 1 колонке)
                    if group_target.lower() in " ".join(r).lower():
                        # Проверяем, что это не просто строка с названием группы, а строка с парой
                        # Обычно в строке с парой заполнено поле с предметом (индекс 1 или 2)
                        subject = r[1] if r[1] else r[2]
                        if len(subject) > 5: # Если название предмета длинное, значит это пара
                            schedule.append({
                                "time": r[4] if len(r) > 4 and r[4] else "См. расп.",
                                "subject": subject,
                                "para": f"Пара {r[2]}" if r[2] and len(r[2]) < 3 else "Замена",
                                "aud": r[3] if len(r) > 3 and r[3] else "—"
                            })
            
            return jsonify(schedule if schedule else [{"subject": "Замен нет", "time": "OK"}])
    except Exception as e:
        return jsonify([{"subject": "Ошибка", "time": "ERR"}])

if __name__ == '__main__':
    app.run()
