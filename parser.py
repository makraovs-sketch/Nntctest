import re

def clean_data(raw_line, group_name):
    """
    Очистка и парсинг строки с расписанием.
    
    Args:
        raw_line: строка из PDF
        group_name: название группы
    
    Returns:
        dict: словарь с полями course, group, teacher, subject, room
    """
    # 1. Извлекаем кабинет (3 цифры или спец. обозначения)
    room_pattern = re.compile(
        r'(\b\d{3}\b|актовый зал|актовый\s+зал|с/з|ук\s+км|2\s+площадка|каб\.?\s*\d{3})',
        re.IGNORECASE
    )
    room_match = room_pattern.search(raw_line.lower())
    room = room_match.group(1).upper() if room_match else "НЕ УКАЗАН"
    
    # Чистим номер кабинета от лишних слов
    room = re.sub(r'КАБ\.?\s*', '', room).strip()
    
    # 2. Извлекаем преподавателя (Фамилия И.О. или И.О. Фамилия)
    teacher_pattern = re.compile(
        r'([А-Я][а-я]+\s[А-Я]\.[А-Я]\.)|([А-Я]\.[А-Я]\.\s[А-Я][а-я]+)'
    )
    teacher_match = teacher_pattern.search(raw_line)
    teacher = teacher_match.group(0) if teacher_match else "Не указан"
    
    # 3. Извлекаем предмет (всё, что осталось после удаления кабинета и препода)
    subject = raw_line
    
    # Удаляем кабинет
    if room_match:
        subject = re.sub(room_pattern, '', subject, flags=re.IGNORECASE)
    
    # Удаляем преподавателя
    if teacher_match:
        subject = subject.replace(teacher_match.group(0), '')
    
    # Удаляем группу (если она есть в строке)
    subject = subject.replace(group_name, '')
    
    # Чистим лишние символы
    subject = re.sub(r'[-–—]\s*$', '', subject)  # тире в конце
    subject = re.sub(r'^\s*[-–—]\s*', '', subject)  # тире в начале
    subject = re.sub(r'\s+', ' ', subject)  # множественные пробелы
    subject = subject.strip(' -–—,;')
    
    # Если предмет пустой — подставляем "Дисциплина"
    if not subject:
        subject = "Дисциплина"
    
    # 4. Определяем курс по первой цифре группы
    course = group_name[0] if group_name and group_name[0].isdigit() else "1"
    
    # Дополнительная проверка: если группа начинается с 1-4, берем эту цифру
    if course in ['1', '2', '3', '4']:
        course = course
    else:
        # Если первая цифра не 1-4, пытаемся найти курс в названии
        course_match = re.search(r'[1-4]', group_name)
        course = course_match.group(0) if course_match else "1"
    
    return {
        "course": int(course),  # возвращаем как int
        "group": group_name,
        "teacher": teacher,
        "subject": subject,
        "room": room
    }


# Пример использования
if __name__ == "__main__":
    test_cases = [
        ("213 Иванов И.И. Математика", "1ИСИП-25-1"),
        ("Актовый зал Петрова А.А. Литература", "2РЭУС-24-2"),
        ("с/з Сидоров С.С. Физика", "3ТОР-23-1к"),
        ("ук км", "4СЭЗС-22-2"),
    ]
    
    for line, group in test_cases:
        result = clean_data(line, group)
        print(f"Группа: {result['group']}")
        print(f"  Курс: {result['course']}")
        print(f"  Кабинет: {result['room']}")
        print(f"  Преподаватель: {result['teacher']}")
        print(f"  Предмет: {result['subject']}")
        print()
