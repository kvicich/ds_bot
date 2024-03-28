import json
import os

# Функция для ввода данных о новом майнере
def input_new_miner():
    print("Введите данные о новом майнере:")
    print("Цикл равняется 5 минутам")
    name = input("Имя майнера: ")
    hashrate = input("Хешрейт в цикл (например, '98'): ")
    price = float(input("Цена: "))
    electricity_consumption = input("Потребление электроэнергии за цикл (например, '12$'): ")
    supported_cryptos = input("Поддерживаемые криптовалюты (через запятую, без пробелов): ").split(',')
    
    # Создание нового майнера в формате словаря
    new_miner = {
        "price": price,
        "hashrate": hashrate,
        "electricity_consumption": electricity_consumption,
        "supported_cryptos": [crypto.strip() for crypto in supported_cryptos]
    }
    
    # Проверяем существование файла и загружаем данные из JSON-файла
    file_path = "miners_data.json"
    if not os.path.exists(file_path):
        with open(file_path, "w", encoding='utf-8') as file:
            json.dump({}, file, ensure_ascii=False)  # Создаем пустой JSON-файл, если его нет
    
    try:
        with open(file_path, "r", encoding='utf-8') as file:
            miners_data = json.load(file)
    except (json.JSONDecodeError, FileNotFoundError):
        # Если файл пустой или его формат поврежден, используем пустой словарь
        miners_data = {}
    
    # Добавление нового майнера в список майнеров
    miners_data[name] = new_miner
    
    # Сохранение обновленных данных в JSON-файл
    with open(file_path, "w", encoding='utf-8') as file:
        json.dump(miners_data, file, indent=4, ensure_ascii=False)
    
    print(f"Майнер {name} успешно добавлен!")

# Вызов функции для ввода данных о новом майнере и добавления его в JSON-файл
input_new_miner()
