import pdfplumber
import requests
import json
import re

# ==========================================================
# КОНФИГУРАЦИЯ
# ==========================================================
# Вставь сюда свою ссылку, которую получил в Google Apps Script
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwLx5inlrUubw53BHrljS81hHGdHm9fCXxj52Ia5r1dKgvn-U8ykL4wge4arhAQkoMnkg/exec"

# Ссылка на файл (можно оставить эту для теста или заменить на актуальную с сайта)
PDF_URL = "https://cloud.nntc.nnov.ru/index.php/s/fYpXD39YccFB5gM/download/%D1%81%D0%B0%D0%B9%D1%82%20zameny2022-2023dist.pdf" 

def parse_schedule():
    print("Скачиваю расписание...")
    try:
        response = requests.get(PDF_URL, timeout=15)
        with open("temp.pdf", "wb") as f:
            f.write(response.content)
    except Exception as e:
        print(f"Ошибка при скачивании: {e}")
        return None

    results = []
    # Регулярка для групп типа 1ИСИП-25-1, 4РЭУС-22-2 и т.д.
    group_regex = re.compile(r'\d[А-ЯA-Z]{2,5}-\d{2}-\d{1,2}к?')
    
    # Регулярка для кабинетов (цифры, залы, площадки)
    room_regex = re.compile(r'(\b\d{3}\b|актовый зал|ук км|2 площадка|кабинет \d+|с/з|219/212)')

    print("Начинаю чтение PDF...")
    with pdfplumber.open("temp.pdf") as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text: continue
            
            lines = text.split('\n')
            current_group = None
            
            for line in lines:
                # 1. Проверяем, нет ли в строке названия группы
                group_match = group_regex.search(line)
                if group_match:
                    current_group = group_match.group(0)
                
                # 2. Проверяем наличие кабинета
                room_match = room_regex.search(line.lower())
                
                # 3. Если нашли и то, и другое — сохраняем
                if room_match and current_group:
                    room_raw = room_match.group(0).strip()
                    # Убираем лишние слова, чтобы в навигаторе был только номер
                    room_id = re.sub(r'кабинет\s+', '', room_raw).upper()
                    
                    results.append({
                        "id": room_id,
                        "subject": current_group,
                        "teacher": line[:40].strip() # Кусочек строки для описания
                    })

    # Убираем дубликаты
    unique_data = {f"{r['id']}{r['subject']}": r for r in results}.values()
    return list(unique_data)

# Запуск
if __name__ == "__main__":
    data = parse_schedule()
    if data:
        print(f"Найдено записей: {len(data)}. Отправляю в Google...")
        
        # Отправляем данные в таблицу
        try:
            payload = {"data": json.dumps(data)}
            res = requests.get(SCRIPT_URL, params=payload)
            print(f"Ответ сервера: {res.text}")
        except Exception as e:
            print(f"Ошибка отправки: {e}")
    else:
        print("Данные не найдены.")
