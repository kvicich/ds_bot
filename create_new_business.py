import json

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
    
    # Загрузка данных из JSON-файла
    with open("business_data.json", "r") as file:
        business_data = json.load(file)
    
    # Добавление нового майнера в список майнеров
    business_data[name] = new_business
    
    # Сохранение обновленных данных в JSON-файл
    with open("business_data.json", "w") as file:
        json.dump(business_data, file, indent=4)
    
    print(f"Бизнес {name} успешно добавлен!")

# Вызов функции для ввода данных о новом бизнесе и добавления его в JSON-файл
input_new_business()