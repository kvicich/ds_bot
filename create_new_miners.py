import json

# Функция для ввода данных о новом майнере
def input_new_miner():
    print("Введите данные о новом майнере:")
    name = input("Имя майнера: ")
    hashrate = input("Хешрейт (в формате 'число/единица времени', например, '98/s'): ")
    price = float(input("Цена: "))
    electricity_consumption = input("Потребление электроэнергии (в формате 'число/единица времени', например, '12$/h'): ")
    supported_cryptos = input("Поддерживаемые криптовалюты (через запятую, без пробелов): ").split(',')
    
    # Создание нового майнера в формате словаря
    new_miner = {
        "price": price,
        "hashrate": hashrate,
        "electricity_consumption": electricity_consumption,
        "supported_cryptos": [crypto.strip() for crypto in supported_cryptos]
    }
    
    # Загрузка данных из JSON-файла
    with open("miners_data.json", "r") as file:
        miners_data = json.load(file)
    
    # Добавление нового майнера в список майнеров
    miners_data[name] = new_miner
    
    # Сохранение обновленных данных в JSON-файл
    with open("miners_data.json", "w") as file:
        json.dump(miners_data, file, indent=4)
    
    print(f"Майнер {name} успешно добавлен!")

# Вызов функции для ввода данных о новом майнере и добавления его в JSON-файл
input_new_miner()
