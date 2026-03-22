import pdfplumber
import requests
import json
import re

# === НАСТРОЙКИ ===
# 1. Вставь сюда свою ссылку из Google Apps Script (после New Deployment)
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbycecQjF9Di-MauPSkN54A2O_q-RUNYiOIlXj3aQmdff8jzwVyYsh66lMIn8UJJ9ihpcg/exec"

# 2. Прямая ссылка на PDF из облака ННТК
PDF_URL = "https://cloud.nntc.nnov.ru/index.php/s/fYpXD39YccFB5gM/download/%D1%81%D0%B0%D0%B9%D1%82%20zameny2022-2023dist.pdf"

def parse_schedule():
    print("--- Шаг 1: Загрузка файла ---")
    try:
        # Маскируемся под браузер, чтобы облако не блокировало запрос
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(PDF_URL, headers=headers, timeout=60)
        response.raise_for_status()
        with open("temp.pdf", "wb") as f:
            f.write(response.content)
        print("Файл успешно скачан.")
    except Exception as e:
        print(f"Ошибка при скачивании файла: {e}")
        return None

    results = []
    # Регулярки для поиска групп и кабинетов
    group_pattern = re.compile(r'(\d[А-ЯA-Z]{2,5}-\d{2}-\d{1,2}к?)')
    room_pattern = re.compile(r'(\d{3}\b|актовый зал|ук км|2 площадка|с/з|каб\.\s*\d+)')

    print("--- Шаг 2: Чтение PDF ---")
    try:
        with pdfplumber.open("temp.pdf") as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue
                
                lines = text.split('\n')
                current_group = None
                
                for line in lines:
                    # Ищем группу в строке
                    group_match = group_pattern.search(line)
                    if group_match:
                        current_group = group_match.group(1)
                    
                    # Ищем кабинет
                    room_match = room_pattern.search(line.lower())
                    
                    # Если нашли и кабинет, и знаем группу — сохраняем
                    if room_match and current_group:
                        room_id = room_match.group(1).upper()
                        # Чистим номер кабинета от лишних слов
                        clean_room = room_id.replace('КАБ.', '').strip()
                        
                        results.append({
                            "id": clean_room,
                            "subject": current_group,
                            "teacher": line.strip()[:50] # Берем начало строки для инфо
                        })
    except Exception as e:
        print(f"Ошибка при парсинге PDF: {e}")
        return None

    # Убираем дубликаты (чтобы не спамить в таблицу)
    unique_data = {f"{r['id']}{r['subject']}": r for r in results}.values()
    return list(unique_data)

if __name__ == "__main__":
    data = parse_schedule()
    
    if data and len(data) > 0:
        print(f"--- Шаг 3: Отправка данных ---")
        print(f"Найдено записей: {len(data)}")
        
        try:
            # Отправляем через POST (в теле запроса), чтобы не было ошибки 400
            response = requests.post(
                SCRIPT_URL, 
                data=json.dumps(data),
                headers={'Content-Type': 'application/json'}
            )
            print(f"Ответ от Google Таблицы: {response.text}")
        except Exception as e:
            print(f"Ошибка при отправке в Google: {e}")
    else:
        print("--- Ошибка: Данные не найдены или файл пуст ---")

