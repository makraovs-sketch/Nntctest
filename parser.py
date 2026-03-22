import pdfplumber
import requests
import json
import re

# === НАСТРОЙКИ ===
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbycecQjF9Di-MauPSkN54A2O_q-RUNYiOIlXj3aQmdff8jzwVyYsh66lMIn8UJJ9ihpcg/exec"
FILE_NAME = "schedule.pdf" # Файл должен лежать в репозитории с таким именем

def parse_schedule():
    results = []
    group_pattern = re.compile(r'(\d[А-ЯA-Z]{2,5}-\d{2}-\d{1,2}к?)')
    room_pattern = re.compile(r'(\d{3}\b|актовый зал|ук км|2 площадка|с/з|каб\.\s*\d+)')

    print(f"--- Чтение локального файла {FILE_NAME} ---")
    try:
        with pdfplumber.open(FILE_NAME) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text: continue
                
                lines = text.split('\n')
                current_group = None
                
                for line in lines:
                    group_match = group_pattern.search(line)
                    if group_match:
                        current_group = group_match.group(1)
                    
                    room_match = room_pattern.search(line.lower())
                    if room_match and current_group:
                        room_id = room_match.group(1).upper()
                        clean_room = room_id.replace('КАБ.', '').strip()
                        
                        results.append({
                            "id": clean_room,
                            "subject": current_group,
                            "teacher": line.strip()[:50]
                        })
    except Exception as e:
        print(f"Ошибка при открытии PDF: {e}")
        return None

    unique_data = {f"{r['id']}{r['subject']}": r for r in results}.values()
    return list(unique_data)

if __name__ == "__main__":
    data = parse_schedule()
    if data and len(data) > 0:
        print(f"Найдено записей: {len(data)}. Отправляю в Google...")
        try:
            response = requests.post(
                SCRIPT_URL, 
                data=json.dumps(data),
                headers={'Content-Type': 'application/json'}
            )
            print(f"Ответ таблицы: {response.text}")
        except Exception as e:
            print(f"Ошибка отправки: {e}")
    else:
        print("Данные не найдены. Проверь имя файла и содержимое.")
