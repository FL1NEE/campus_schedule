# -*- coding: utf-8 -*-
import re
import requests
import datetime
from bs4 import BeautifulSoup

def scrape_schedule():
    HEADERS: dict = \
    {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
    }
    URL: str = "https://www.kstu.ru/www_Ggrid.jsp"
    PARAMS: dict = \
    {
        "f": "224", # возможно это номер института
        "d": str(datetime.date.today()),
        "g": "41562", # возможно это номер группы
        "idk": "55951" # static data
    }
    RESPONSE: str = requests.get(
        URL, 
        params = PARAMS,
        headers = HEADERS
    )
    RESPONSE.encoding = 'utf-8'
    return RESPONSE.text

def parse_schedule(html_content, target_date):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Выбираем десктопную таблицу
    table = soup.find('table', class_='brstu-table', attrs={'class': ['brstu-table', 'd-none', 'd-md-block']})
    if not table:
        return []
    
    rows = table.find_all('tr')
    schedule = []
    
    # Извлекаем заголовки дней с помощью регулярных выражений
    header_row = rows[0]
    headers = []
    for th in header_row.find_all('td')[1:]:  # Пропускаем первый столбец с временем
        header_text = th.get_text(strip=True)
        date_match = re.match(r'\d{2}\.\d{2}\.\d{4}', header_text)
        if date_match:
            headers.append(date_match.group())
    
    for row in rows[1:]:
        cells = row.find_all('td')
        if not cells:
            continue
        time_cell = cells[0].get_text(strip=True).split('\n')[0].strip()
        
        for idx, cell in enumerate(cells[1:]):  # Пропускаем первую ячейку с временем
            if idx >= len(headers):
                break  # На случай, если количество ячеек не совпадает с заголовками
            current_date = headers[idx]
            
            if target_date and current_date != target_date:
                continue
            
            lessons = []
            # Ищем все div с информацией о парах
            for div in cell.find_all('div', style=re.compile(r'max-width:180')):
                lesson_text = div.get_text(separator='\n', strip=True).split('\n')
                
                # Пропускаем пустые или неполные записи
                if len(lesson_text) < 3:
                    continue
                
                # Извлекаем данные
                room = lesson_text[0].strip()
                subject = lesson_text[1].strip()
                teacher = lesson_text[-1].split('(')[-1].replace(')', '').strip()
                
                lessons.append({
                    'Время': time_cell,
                    'Аудитория': room,
                    'Предмет': subject,
                    'Преподаватель': teacher
                })
            
            if lessons:
                schedule.append({
                    'Дата': current_date,
                    'Пары': lessons
                })
    
    return schedule

# Параметры для проверки
target_date = '06.05.2025'
html_content = scrape_schedule()
schedule = parse_schedule(html_content, target_date)

# Вывод результатов
data = {"date": target_date, "lessons": []}
if schedule:
    for day in schedule:
        for lesson in day["Пары"]:
            data["lessons"].append({"time": str(lesson["Время"]).replace("пара", "пара "), "auditorium": lesson["Аудитория"], "subject": lesson["Предмет"], "teacher": lesson['Преподаватель']})

print(data)#{'date': '06.05.2025', 'lessons': [{'time': '1 пара 08:00-09:30', 'auditorium': 'Г-507', 'subject': 'Иностранный язык (ПЗ)', 'teacher': 'Кузнецова М.Н.'}, {'time': '2 пара 09:40-11:10', 'auditorium': 'М-6(12)', 'subject': 'Элективные курсы по физической культуре и спорту (ПЗ)', 'teacher': 'Куршев А.В.'}, {'time': '3 пара 11:20-12:50', 'auditorium': 'Л-209', 'subject': 'Высшая математика (ЛЕКЦ)', 'teacher': 'Еникеева С.Р.'}, {'time': '4 пара 13:00-14:30', 'auditorium': 'Д-110', 'subject': 'Физика (ПЗ)', 'teacher': 'Иванова А.А.'}]}
