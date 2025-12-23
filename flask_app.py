from flask import Flask, jsonify, request
import pdfplumber
import requests
import io

app = Flask(__name__)
# Чтобы в браузере сразу были русские буквы
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
                    # Чистим данные от пустых ячеек и переносов строк
                    r = [str(c).replace('\n', ' ').strip() if c else "" for c in row]
                    
                    # Ищем строку, где упоминается ваша группа
                    if group_target.lower() in " ".join(r).lower():
                        # Проверяем, что это не пустая строка (обычно предмет в колонке 1 или 2)
                        subject_name = r[1] if len(r) > 1 and len(r[1]) > 3 else r[2]
                        
                        if len(subject_name) > 3: # Если название предмета похоже на правду
                            schedule.append({
                                "time": r[4] if len(r) > 4 and r[4] else "08:10",
                                "subject": subject_name,
                                "para": f"Пара {r[2]}" if r[2] and len(r[2]) < 3 else "Замена",
                                "aud": r[3] if len(r) > 3 and r[3] else "—"
                            })
            
            # Если ничего не нашли
            if not schedule:
                return jsonify([{"subject": "Замен не обнаружено", "time": "ОК"}])
                
            return jsonify(schedule)
            
    except Exception as e:
        return jsonify([{"subject": "Ошибка доступа к PDF", "time": "ERR"}])

if __name__ == '__main__':
    app.run()

