import pdfplumber
import requests
import json
import re

# Твои настройки
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyeY1vTeLcli6EdhxaMT4oYshKZRJHFy5swO-eyt3fe7TW-v2I5qGCBpnwhOuNgArS4eA/exec"
PDF_URL = "https://cloud.nntc.nnov.ru/index.php/s/fYpXD39YccFB5gM/download/%D1%81%D0%B0%D0%B9%D1%82%20zameny2022-2023dist.pdf"

def parse_schedule():
    print("Скачиваю файл из облака...")
    try:
        # Добавляем заголовки, чтобы облако не блокировало бота
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(PDF_URL, headers=headers, timeout=30)
        with open("temp.pdf", "wb") as f:
            f.write(response.content)
    except Exception as e:
        print(f"Ошибка скачивания: {e}")
        return None

    results = []
    # Регулярки для групп и кабинетов (учитываем с/з, актовый зал и т.д.)
    group_pattern = re.compile(r'(\d[А-ЯA-Z]{2,5}-\d{2}-\d{1,2}к?)')
    room_pattern = re.compile(r'(\d{3}\b|актовый зал|ук \d{3}|ук км|2 площадка|с/з|каб\.\s*\d+)')

    print("Читаю страницы...")
    with pdfplumber.open("temp.pdf") as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text: continue
            
            lines = text.split('\n')
            current_group = None
            
            for line in lines:
                # 1. Проверяем, не является ли строка названием группы
                group_match = group_pattern.search(line)
                if group_match:
                    current_group = group_match.group(1)
                
                # 2. Ищем кабинет
                room_match = room_pattern.search(line.lower())
                
                # 3. Если есть и то и другое — сохраняем
                if room_match and current_group:
                    room_id = room_match.group(1).upper()
                    # Чистим ID от лишних слов
                    clean_id = room_id.replace('КАБ.', '').strip()
                    
                    results.append({
                        "id": clean_id,
                        "subject": current_group,
                        "teacher": line[:40] # Начало строки для описания
                    })

    # Убираем дубликаты
    unique = {f"{r['id']}{r['subject']}": r for r in results}.values()
    return list(unique)

if __name__ == "__main__":
    data = parse_schedule()
    if data:
        print(f"Найдено {len(data)} записей. Отправляю в Google...")
        payload = {"data": json.dumps(data)}
        r = requests.get(SCRIPT_URL, params=payload)
        print("Результат:", r.text)
    else:
        print("Данные не найдены. Проверь код парсера.")
