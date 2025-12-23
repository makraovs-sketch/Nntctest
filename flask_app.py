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
    if not group_target: return jsonify([])

    try:
        response = requests.get(PDF_URL, timeout=15)
        with pdfplumber.open(io.BytesIO(response.content)) as pdf:
            schedule = []
            for page in pdf.pages:
                table = page.extract_table()
                if not table: continue
                
                for row in table:
                    # Чистим ячейки от лишних пробелов и переносов
                    r = [str(c).replace('\n', ' ').strip() if c else "" for c in row]
                    
                    # Если в строке нашли номер твоей группы
                    if group_target.lower() in " ".join(r).lower():
                        # Пытаемся найти предмет (обычно самая длинная строка, но не название группы)
                        potential_subject = ""
                        for cell in r:
                            if len(cell) > 5 and group_target not in cell:
                                potential_subject = cell
                                break
                        
                        schedule.append({
                            "group": group_target,
                            "para_num": r[2] if len(r) > 2 and len(r[2]) < 3 else (r[0] if len(r[0]) < 3 else "—"),
                            "subject": potential_subject if potential_subject else "Замена",
                            "teacher": r[3] if len(r) > 3 and len(r[3]) > 3 else "—",
                            "aud": r[5] if len(r) > 5 else (r[4] if "каб" in r[4].lower() or r[4].isdigit() else "—"),
                            "time": r[4] if len(r) > 4 and ":" in r[4] else "—"
                        })
            
            return jsonify(schedule if schedule else [{"subject": "Замен не найдено"}])
    except Exception as e:
        return jsonify([{"subject": "Ошибка: " + str(e)}])

if __name__ == '__main__':
    app.run()

