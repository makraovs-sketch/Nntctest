import re

def clean_data(raw_line, group_name):
    # 1. Паттерн кабинета
    room_pattern = re.compile(
        r'(\b\d{3}\b|актовый зал|актовый\s+зал|с/з|ук\s+км|2\s+площадка|каб\.?\s*\d{3})',
        re.IGNORECASE
    )
    
    room_match = room_pattern.search(raw_line)
    room = room_match.group(1).upper() if room_match else "НЕ УКАЗАН"
    
    # Чистка номера (убираем "каб.")
    room = re.sub(r'КАБ\.?\s*', '', room, flags=re.IGNORECASE).strip()
    
    # 2. Паттерн преподавателя
    teacher_pattern = re.compile(
        r'([А-Я][а-я]+\s[А-Я]\.[А-Я]\.)|([А-Я]\.[А-Я]\.\s[А-Я][а-я]+)'
    )
    teacher_match = teacher_pattern.search(raw_line)
    teacher = teacher_match.group(0) if teacher_match else "Не указан"
    
    # 3. Извлекаем предмет
    subject = raw_line
    if room_match:
        subject = room_pattern.sub('', subject)
    if teacher_match:
        subject = subject.replace(teacher_match.group(0), '')
    
    # Удаляем название группы, если оно затесалось в строку
    subject = subject.replace(group_name, '')
    
    # Чистка мусора
    subject = re.sub(r'\s+', ' ', subject) # Двойные пробелы
    subject = subject.strip(' -–—,;')
    
    if not subject or subject.isspace():
        subject = "Дисциплина"
    
    # 4. Определяем курс (логика по цифре 1-4)
    course_match = re.search(r'[1-4]', group_name)
    course = course_match.group(0) if course_match else "1"
    
    return {
        "course": int(course),
        "group": group_name,
        "teacher": teacher,
        "subject": subject,
        "room": room
    }

# Твои тесты пройдут идеально
