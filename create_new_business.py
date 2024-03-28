import json
import os

# Функция для ввода данных о новом бизнесе
def input_new_business():
    print("Введите данные о новом бизнесе:")
    name = input("Имя бизнеса: ")
    income = input("Доход в 30 минут (например, '1500'): ")
    price = float(input("Цена: "))
    consumption = input("Потребление ресурсов (например, '150'): ")
    
    # Создание бизнеса в формате словаря
    new_business = {
        "price": price,
        "income": income,
        "consumption": consumption,
    }
    
    # Проверяем существование файла
    file_path = "business_data.json"
    if not os.path.exists(file_path):
        with open(file_path, "w", encoding='utf-8') as file:
            json.dump({}, file, ensure_ascii=False)  # Создаем пустой JSON-файл, если его нет
    
    # Загрузка данных из JSON-файла
    try:
        with open(file_path, "r", encoding='utf-8') as file:
            business_data = json.load(file)
    except (json.JSONDecodeError, FileNotFoundError):
        # Если файл пустой или его формат поврежден, используем пустой словарь
        business_data = {}
    
    # Добавление нового бизнеса в словарь
    business_data[name] = new_business
    
    # Сохранение обновленных данных в JSON-файл
    with open(file_path, "w", encoding='utf-8') as file:
        json.dump(business_data, file, indent=4, ensure_ascii=False)
    
    print(f"Бизнес {name} успешно добавлен!")

# Вызов функции для ввода данных о новом бизнесе и добавления его в JSON-файл
input_new_business()
