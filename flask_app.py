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
                    # Чистим все ячейки в строке
                    r = [str(c).replace('\n', ' ').strip() for c in row if c]
                    full_row_text = " ".join(r)
                    
                    if group_target.lower() in full_row_text.lower():
                        # Простая логика: если в ячейке есть ":", это время. 
                        # Если ячейка из 1-3 цифр — это кабинет или пара.
                        time_val = next((x for x in r if ":" in x), "—")
                        para_val = next((x for x in r if x.isdigit() and len(x) == 1), "—")
                        aud_val = next((x for x in r if (x.isdigit() and len(x) > 1) or "каб" in x.lower()), "—")
                        
                        # Предмет — обычно самая длинная часть строки, которая не группа
                        subj = "Замена"
                        for x in r:
                            if len(x) > 10 and group_target not in x:
                                subj = x
                                break

                        schedule.append({
                            "group": group_target,
                            "para_num": para_val,
                            "subject": subj,
                            "teacher": "См. расписание",
                            "aud": aud_val,
                            "time": time_val
                        })
            
            return jsonify(schedule if schedule else [{"subject": "Замен нет", "time": "ОК"}])
    except Exception as e:
        return jsonify([{"subject": "Ошибка: " + str(e)}])

if __name__ == '__main__':
    app.run()

