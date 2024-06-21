import os
import json
import disnake
from disnake.ext import commands
import logging
import random
import time
import asyncio

# Переменные
START_TIME = time.time() # Время запуска (для /bot_stats)
SERVERS_DATA_DIR = "servers_data"  # Папка с данными серверов
WORK_COOLDOWN = 150 # Время в секундах между попытками зароботка для /sidejob
WORK_INCOME = 25, 234 # Заработок с /sidejob
WORK_TIMEOUT = 25 # Таймаут в /work
STEAL_COOLDOWN = 300  # Время в секундах между попытками кражи
STEAL_INCOME = 50, 500 # Заработок с /steal
FAILED_STEAL_MIN_LOSS = 15 # Минимальная потеря монет в /steal
FAILED_STEAL_MAX_LOSS = 350 # Максимальная потеря монет в /steal
MINERS_DATA_PATH = "miners_data.json" # Файл с датой майнеров
BUSINESS_DATA_PATH = "business_data.json" # Файл с информацией о майнерах
BUSINESS_COOLDOWN = 900  # Время обновления бизнесов в секундах 60 секунд = 1 минута
INFO_COOLDOWN = 120 # Время в секундах между запросом информации о майнерах/бизнесах
APART_COOLDOWN = 3600 # Время в секундах для "взыскания" налогов
APART_DATA_PATH = "apart_data.json" # Файл с данными о апартаментах
SAVE_LOGS = True # Установите в False, если не хотите сохранять логи в файл
UNDER_CONSTRUCTION = "working.txt" # Сообщения для команд в разработке
mining_tasks = {} # Задачи для майнинга
OWNER_ID = "822112444973056011" # Сюда запишите айди овнера бота
VERIFIED_GUILDS = ([1203755517072252989])

def setup_logging():
    # Создаем логгер
    logger = logging.getLogger('discord_bot')
    logger.setLevel(logging.DEBUG)

    # Определяем формат логов
    formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')

    # Настройка для вывода логов на консоль
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if SAVE_LOGS:
        # Настройка для сохранения логов в файл
        file_handler = logging.FileHandler('ds_bot.log')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

# Создаем объект бота
logger = setup_logging()
intents = disnake.Intents.default()
bot = commands.Bot(intents=intents, sync_commands_debug=True)

# После сброса экономики заебись
def ensure_server_data_dir(server_id):
    server_dir = os.path.join(SERVERS_DATA_DIR, str(server_id))
    if not os.path.exists(server_dir):
        os.makedirs(server_dir)

# Штучка, дату юзеров загружать
def load_user_data(server_id, user_id):
    ensure_server_data_dir(server_id)
    data_path = user_data_path(server_id, user_id)
    if os.path.exists(data_path):
        with open(data_path, "r", encoding="UTF-8") as f:
            print("Была загружена дата пользователей")
            return json.load(f)
    else:
        with open(data_path, "w") as f:
            json.dump({}, f)
            print("Загружена дата пользователя")
        return {}

# Эта штука вообще всё за раз грузит, будем использовать
def load_all_user_data():
    all_user_data = {}
    for server_id in os.listdir(SERVERS_DATA_DIR):
        server_data_dir = os.path.join(SERVERS_DATA_DIR, server_id)
        if os.path.isdir(server_data_dir):
            server_users_data = {}
            for user_file in os.listdir(server_data_dir):
                if user_file.endswith(".json"):
                    user_id = user_file.split(".")[0]
                    user_data = load_user_data(int(server_id), user_id)
                    server_users_data[user_id] = user_data
            all_user_data[server_id] = server_users_data
    print("Загружена дата всех пользователей")
    return all_user_data

# А вот эта штучка сохраняет дату юзеров
def save_user_data(server_id, user_id, data):
    ensure_server_data_dir(server_id)
    data_path = user_data_path(server_id, user_id)
    with open(data_path, "w", encoding="UTF-8") as f:
        json.dump(data, f)
        print("Сохранена дата пользователя")

# Вычисляет точное местоположение личного файла юзера
def user_data_path(server_id, user_id):
    return os.path.join(SERVERS_DATA_DIR, str(server_id), f"{user_id}.json")

# Функция для загрузки списка админов, владельцев и тестеров из файла
def load_access_data():
    access_data_path = os.path.join("servers_data", "access_data.json")
    if os.path.exists(access_data_path):
        with open(access_data_path, "r", encoding="UTF-8") as f:
            return json.load(f)
    else:
        return {"admins": [], "testers": []}

# Функция для сохранения списка админов, владельцев и тестеров в файл
def save_access_data(access_data):
    access_data_path = os.path.join("servers_data/access_data.json")
    with open(access_data_path, "w", encoding="UTF-8") as f:
        json.dump(access_data, f, indent=4)

# Обновленная функция для проверки уровня доступа пользователя
def check_access_level(access_level: str, user_id: str) -> bool:
    access_data = load_access_data()
    if access_level.lower() == "owner":
        return user_id == OWNER_ID
    elif access_level.lower() == "admin":
        return user_id in access_data["admins"] or user_id == OWNER_ID
    elif access_level.lower() == "tester":
        return user_id in access_data["testers"] or user_id in access_data["admins"] or user_id == OWNER_ID
    else:
        return False

# Команда для смены уровня доступа пользователя
@bot.slash_command(name='change_access', description="Изменяет уровень доступа пользователя.")
async def change_access(inter, user_id: str, new_level: str):
    if inter.author.id == OWNER_ID:
        await inter.response.send_message("У вас нет доступа к этой команде.")
        return

    result = change_access_level(int(user_id), new_level)
    await inter.response.send_message(result)

# Функция для смены уровня доступа пользователя на уровне бота
def change_access_level(user_id: str, new_level: str):
    access_data = load_access_data()
    if new_level.lower() not in ["admin", "tester"]:
        return "Неизвестный или уровень доступа."
    if new_level.lower() == "admin":
        access_data["admins"].append(user_id)
        access_data["testers"] = [uid for uid in access_data["testers"] if uid != user_id]
    elif new_level.lower() == "tester":
        access_data["testers"].append(user_id)
        access_data["admins"] = [uid for uid in access_data["admins"] if uid != user_id]

    save_access_data(access_data)
    return f"Уровень доступа для пользователя {user_id} изменён на {new_level}."

@bot.slash_command(name='test_access', description="Проверяет уровень доступа пользователя.")
async def test_adm_cmd(inter):
    server_id, user_id = inter.guild_id, str(inter.user.id)

    if server_id not in VERIFIED_GUILDS:
        return "Ваша гильдия не верифицированна, команда не доступна"

    access_levels = ["owner", "admin", "tester"]
    user_access_level = None

    for level in access_levels:
        if check_access_level("admin", user_id):
            user_access_level = level
            break

    if user_access_level:
        await inter.response.send_message(f"Ваш уровень доступа: {user_access_level.capitalize()}")
    else:
        await inter.response.send_message("У вас нет доступа.")

# Асинхронная функция для генерации случайного сообщения
async def randy_random():
    with open(UNDER_CONSTRUCTION, "r", encoding='utf-8') as file:
        messages = file.readlines()
        message = random.choice(messages).strip()
        return message

# Событие выполняющееся после полного запуска бота
@bot.event
async def on_ready():
    await bot.change_presence(activity=disnake.Game(name="Заёбывает юзеров"), status=disnake.Status.idle)
    logger.info("Активность и статус бота изменены")
    logger.info(f"Бот запущен, его имя {bot.user}")

# Команда для подработки
@bot.slash_command(name='sidejob', description="Работка.")
async def SideJob_cmd(inter):
    server_id, user_id = str(inter.guild_id), str(inter.user.id)
    current_time = time.time()
    last_work_time = bot.last_work_time.get(server_id, {})
    if user_id in last_work_time:
        time_elapsed = current_time - last_work_time[user_id]
        if time_elapsed < WORK_COOLDOWN:
            time_left = WORK_COOLDOWN - time_elapsed
            await inter.response.send_message(f'{inter.author.mention}, вы уже работали недавно. Подождите еще {int(time_left)} секунд.')
            return
    last_work_time[user_id] = current_time
    bot.last_work_time[server_id] = last_work_time
    currency_earned = random.randint(WORK_INCOME)
    with open("work_message.txt", "r", encoding="utf-8") as file:
        messages = file.readlines()
        work_message = random.choice(messages).strip()
    user_data = load_user_data(server_id, user_id)
    user_balance = user_data.get("money", 0)
    user_balance += currency_earned
    user_data["money"] = user_balance
    save_user_data(server_id, user_id, user_data)
    work_message = work_message.replace("{currency_earned}", str(currency_earned))
    await inter.response.send_message(f'{inter.author.mention}, {work_message}.')

# Команда для попытки кражи
@bot.slash_command(name='steal', description="Попытка украсть что-то.")
async def steal_cmd(inter):
    server_id, user_id = str(inter.guild_id), str(inter.user.id)
    current_time = time.time()
    last_steal_time = bot.last_steal_time.get(server_id, {})
    if user_id in last_steal_time:
        time_elapsed = current_time - last_steal_time[user_id]
        if time_elapsed < STEAL_COOLDOWN:
            time_left = STEAL_COOLDOWN - time_elapsed
            await inter.response.send_message(f'Вы недавно уже пытались что-то украсть. Подождите еще {int(time_left)} секунд.')
            return
    last_steal_time[user_id] = current_time
    bot.last_steal_time[server_id] = last_steal_time
    if random.random() < 0.5:  # Шанс 50%
        stolen_amount = random.randint(STEAL_INCOME)
        with open("steal_message.txt", "r", encoding="utf-8") as file:
            messages = file.readlines()
            steal_message = random.choice(messages).strip()
        user_data = load_user_data(server_id, user_id)
        user_balance = user_data.get("money", 0)
        user_balance += stolen_amount
        user_data["money"] = user_balance
        save_user_data(server_id, user_id, user_data)
        steal_message = steal_message.replace("{stolen_amount}", str(stolen_amount))
        await inter.response.send_message(f'{inter.author.mention}, {steal_message}')
    else:
        lost_amount = random.randint(FAILED_STEAL_MIN_LOSS, FAILED_STEAL_MAX_LOSS)
        user_data = load_user_data(server_id, user_id)
        user_balance = user_data.get("money", 0)
        user_balance -= lost_amount  
        user_data["money"] = user_balance
        save_user_data(server_id, user_id, user_data)
        await inter.response.send_message(f"Попытка не удалась, вы потеряли {lost_amount} :coin:")
        
@bot.slash_command(name='ping', description="Проверяет ваш пинг.")
async def ping(inter):
    start_time = time.time()
    # Делаем фиктивный запрос, чтобы измерить задержку
    await inter.response.defer()
    end_time = time.time()
    ping_time = round((end_time - start_time) * 1000)
    await inter.edit_original_message(content=f"Понг! :ping_pong:\n"
                                      f"Ваш пинг: {ping_time} мс")

# Команда для просмотра текущих курсов криптовалют
@bot.slash_command(name='crypto_prices', description='Просмотреть текущие курсы криптовалют.')
async def crypto_prices_cmd(inter):
    crypto_list = load_crypto_prices()
    prices_str = '\n'.join([f"{crypto_list[currency]['emoji']} {currency.capitalize()}: {crypto_list[currency]['price']} :coin:" for currency in crypto_list])
    await inter.response.send_message(f"Текущие курсы криптовалют:\n{prices_str}")

# Функция для генерации новых цен криптовалют
def generate_crypto_prices():
    crypto_list = load_crypto_prices()
    for currency in crypto_list:
        change1 = random.uniform(-2, -0.1)
        change2 = random.uniform(0.1, 2)
        change_percent = random.uniform(change1, change2)  # Изменение на случайный процент от -2% до 2%
        if random.random() < 0.09:  # Шанс 9% на редкое изменение
            change1 = random.uniform(0.6, 0.9)
            change2 = random.uniform(1.01, 1.3)
            change_percent *= random.uniform(change1, change2)  # Редкое изменение от -20% до 20%
        crypto_list[currency]['price'] *= (1 + change_percent / 100)  # Применяем изменение
        # Округляем цены криптовалют до 2 знаков после запятой/точки
        crypto_list[currency]['price'] = round(crypto_list[currency]['price'], 2)
    with open("crypto_prices.json", "w") as file:
        json.dump(crypto_list, file)
    logger.info("Изменились цены криптовалют!")

# Цикл меняющий цены раз в 5 минут
async def crypto_prices_generator():
    while True:
        await asyncio.sleep(300)  # Пауза в 5 минут
        generate_crypto_prices()

# Функция для сохранения текущих курсов криптовалют
def save_crypto_prices(crypto_list):
    with open("crypto_prices.json", "w") as file:
        json.dump(crypto_list, file)
        logger.debug("Сохранены курсы криптовалют!")

# Функция для загрузки текущих курсов криптовалют из файла
def load_crypto_prices():
    if os.path.exists("crypto_prices.json"):
        with open("crypto_prices.json", "r") as file:
            logger.debug("Загружены курсы криптовалют!")
            return json.load(file)
    else:
        logger.warn("Загружены начальные курсы криптовалют! Проверьте файл crypto_prices.json!")
        return {"bitcoin": {"emoji": ":dvd:", "price": 50000}, "ethereum": {"emoji": ":cd:", "price": 10000}, "bananacoin": {"emoji": ":banana:", "price": 250}}

CRYPTO_LIST = load_crypto_prices()

@bot.slash_command(name="change_crypto_prices", description='Сменить цены криптовалют.')
async def change_crypto_prices(inter):
    server_id, user_id = inter.guild_id, str(inter.user.id)

    if not check_access_level("admin", user_id):
        await inter.response.send_message("У вас нет доступа к этой команде.")
        return
    
    if server_id not in VERIFIED_GUILDS:
        await inter.response.send_message("Ваша гильдия не верифицированна, команда не доступна")
        return 
    
    logger.info("Кто-то принудительно изменил цены криптовалют!")
    generate_crypto_prices()
    await inter.response.send_message("Вы принудительно изменили цены криптовалют!")

# Команда для выдачи денег
@bot.slash_command(name='give_money', description="Выдает деньги пользователю.")
async def give_money(inter, member: disnake.Member, amount: int):
    # Загрузка данных пользователя
    server_id, user_id = inter.guild_id, str(inter.user.id)
    user_data = load_user_data(server_id, user_id)

    # Проверяем на соответствие уровню допуска
    if not check_access_level("admin", user_id):
        await inter.response.send_message("У вас нет доступа к этой команде.")
        return

    if server_id not in VERIFIED_GUILDS:
        await inter.response.send_message("Ваша гильдия не верифицированна, команда не доступна")
        return 

    # Добавление денег пользователю
    user_data['money'] = user_data.get('money', 0) + amount

    # Отправка сообщения о выдаче денег
    await inter.response.send_message(f'Пользователь {member.mention} (ID: {member.id}) получил {amount} денег.')

    # Сохранение данных пользователя после выдачи денег
    save_user_data(server_id, user_id, user_data)

# Команда для отнятия денег
@bot.slash_command(name='take_money', description="Отнимает деньги у пользователя.")
async def take_money(inter, member: disnake.Member, amount: int):
    # Загрузка данных пользователя
    server_id, user_id = inter.guild_id, str(inter.user.id)
    user_data = load_user_data(server_id, user_id)

    if not check_access_level("admin", user_id):
        await inter.response.send_message("У вас нет доступа к этой команде.")
        return
    
    if server_id not in VERIFIED_GUILDS:
        await inter.response.send_message("Ваша гильдия не верифицированна, команда не доступна")
        return 

    # Проверка достаточности денег у пользователя
    if user_data.get('money', 0) < amount:
        await inter.response.send_message(f'У пользователя {member.mention} (ID: {member.id}) недостаточно денег.')
        return           

    # Отнимание денег у пользователя
    user_data['money'] -= amount

    # Отправка сообщения об отнятии денег
    await inter.response.send_message(f'У пользователя {member.mention} (ID: {member.id}) отняли {amount} денег.')

    # Сохранение данных пользователя после отнятия денег
    save_user_data(server_id, user_id, user_data)

# Команда для выдачи криптовалюты
@bot.slash_command(name='give_crypto', description="Выдает криптовалюту пользователю.")
async def give_crypto(inter, currency: str, member: disnake.Member, amount: int):
    # Проверка наличия указанной криптовалюты в списке
    if currency.lower() not in CRYPTO_LIST:
        await inter.response.send_message(f'Криптовалюта {currency} не найдена в списке доступных криптовалют.')
        return

    # Загрузка данных пользователя
    server_id, user_id = inter.guild_id, str(inter.user.id)
    user_data = load_user_data(server_id, user_id)

    if not check_access_level("admin", user_id):
        await inter.response.send_message("У вас нет доступа к этой команде.")
        return
    
    if server_id not in VERIFIED_GUILDS:
        await inter.response.send_message("Ваша гильдия не верифицированна, команда не доступна")
        return 

    # Добавление указанной криптовалюты пользователю
    user_data[currency.lower()] = user_data.get(currency.lower(), 0) + amount

    # Отправка сообщения о выдаче криптовалюты
    await inter.response.send_message(f'Пользователь {member.mention} (ID: {member.id}) получил {amount} {currency}.')

    # Сохранение данных пользователя после выдачи криптовалюты
    save_user_data(server_id, user_id, user_data)

# Команда для отнятия криптовалюты
@bot.slash_command(name='take_crypto', description="Отнимает криптовалюту у пользователя.")
async def take_crypto(inter, currency: str, member: disnake.Member, amount: int):
    # Проверка наличия указанной криптовалюты в списке
    if currency.lower() not in CRYPTO_LIST:
        await inter.response.send_message(f'Криптовалюта {currency} не найдена в списке доступных криптовалют.')
        return

    # Загрузка данных пользователя
    server_id, user_id = inter.guild_id, str(inter.user.id)
    user_data = load_user_data(server_id, user_id)

    if not check_access_level("admin", user_id):
        await inter.response.send_message("У вас нет доступа к этой команде.")
        return
    
    if server_id not in VERIFIED_GUILDS:
        await inter.response.send_message("Ваша гильдия не верифицированна, команда не доступна")
        return 

    # Проверка достаточности указанной криптовалюты у пользователя
    if user_data.get(currency.lower(), 0) < amount:
        await inter.response.send_message(f'У пользователя {member.mention} (ID: {member.id}) недостаточно {currency}.')
        return

    # Отнимание указанной криптовалюты у пользователя
    user_data[currency.lower()] -= amount

    # Отправка сообщения об отнятии криптовалюты
    await inter.response.send_message(f'У пользователя {member.mention} (ID: {member.id}) отняли {amount} {currency}.')

    # Сохранение данных пользователя после отнятия криптовалюты
    save_user_data(server_id, user_id, user_data)

def load_promo_codes():
    with open('promocodes.txt', 'r') as file:
        codes = {}
        for line in file:
            promo, action = line.strip().split(' - ')
            codes[promo] = action
    return codes

@bot.slash_command(name="promo", description='Позволяет ввести промокод.')
async def promo(inter, code: str):
    server_id, user_id = str(inter.guild_id), str(inter.user.id)
    user_data = load_user_data(server_id, user_id)
    used_promocodes = user_data.get('used_promocodes', [])
    promo_codes = load_promo_codes()  

    # Проверка на использование промокода
    if code in used_promocodes:
        await inter.response.send_message("Промокод уже использован.")
        return

    if code in promo_codes:
        action = promo_codes[code]
        try:
            value, key = action.split(' =+ ')
        except ValueError:
            await inter.response.send_message("Неправильный формат действия промокода.")
            return

        if key == 'money':
            user_data['money'] = user_data.get('money', 0) + float(value)
            await inter.response.send_message(f"Вы получили {value} денег.")
        elif key in ['bitcoin', 'ethereum', 'bananacoin']:
            user_data[key] = user_data.get(key, 0) + float(value)
            await inter.response.send_message(f"Вы получили {value} {key}.")
        else:
            await inter.response.send_message("Произошла ошибка при обработке промокода.")

        used_promocodes.append(code)
        user_data['used_promocodes'] = used_promocodes
    else:
        await inter.response.send_message("Промокод не найден.")
    save_user_data(server_id, user_id, user_data)
    
@bot.slash_command(name="exchange", description='Позволяет обменивать валюты')
async def exchange_cmd(inter, source_currency: str, target_currency: str, amount: float):
    # Проверяем, что валюты из списка доступных
    if source_currency.lower() not in CRYPTO_LIST and source_currency.lower() != "money":
        await inter.response.send_message(f"Валюта {source_currency} не найдена в списке доступных криптовалют и денег.")
        return

    # Обрабатываем случай обмена денег на криптовалюту
    if source_currency.lower() == "money":
        # Проверяем, что пользователь имеет достаточно денег для обмена
        server_id, user_id = str(inter.guild_id), str(inter.user.id)
        user_data = load_user_data(server_id, user_id)
        if user_data.get("money", 0) < amount:
            await inter.response.send_message("У вас недостаточно денег для обмена.")
            return

        # Вычисляем сумму после обмена
        target_rate = CRYPTO_LIST[target_currency.lower()]["price"]
        exchanged_amount = amount / target_rate
        exchanged_rounded_amount = round(exchanged_amount, 6)

        # Выполняем обмен
        user_data["money"] -= amount
        user_data[target_currency.lower()] = user_data.get(target_currency.lower(), 0) + exchanged_rounded_amount

        # Сообщаем пользователю об успешном обмене
        await inter.response.send_message(f"Вы успешно обменяли {amount} денег на {exchanged_rounded_amount} {target_currency}.")

        # Сохраняем данные пользователя после обмена
        save_user_data(server_id, user_id, user_data)
    
    # Обрабатываем случай обмена криптовалюты на деньги
    elif target_currency.lower() == "money":
        # Проверяем, что пользователь имеет достаточно криптовалюты для обмена
        server_id, user_id = str(inter.guild_id), str(inter.user.id)
        user_data = load_user_data(server_id, user_id)
        if user_data.get(source_currency.lower(), 0) < amount:
            await inter.response.send_message(f"У вас недостаточно {source_currency} для обмена.")
            return

        # Вычисляем сумму после обмена
        source_rate = CRYPTO_LIST[source_currency.lower()]["price"]
        exchanged_amount = amount * source_rate
        exchanged_rounded_amount = round(exchanged_amount, 5)

        # Выполняем обмен
        user_data["money"] = user_data.get("money", 0) + exchanged_rounded_amount
        user_data[source_currency.lower()] -= amount

        # Сообщаем пользователю об успешном обмене
        await inter.response.send_message(f"Вы успешно обменяли {amount} {source_currency} на {exchanged_rounded_amount} денег.")

        # Сохраняем данные пользователя после обмена
        save_user_data(server_id, user_id, user_data)
    
    # Обрабатываем обмен криптовалюты на криптовалюту
    else:
        # Получаем текущие курсы валют из списка
        source_rate = CRYPTO_LIST[source_currency.lower()]["price"]
        target_rate = CRYPTO_LIST[target_currency.lower()]["price"]

        # Проверяем, что пользователь имеет достаточно криптовалюты для обмена
        server_id, user_id = str(inter.guild_id), str(inter.user.id)
        user_data = load_user_data(server_id, user_id)
        if user_data.get(source_currency.lower(), 0) < amount:
            await inter.response.send_message(f"У вас недостаточно {source_currency} для обмена.")
            return

        # Выполняем обмен
        exchanged_amount = amount * (source_rate / target_rate)
        exchanged_rounded_amount = round(exchanged_amount, 5)
        user_data[source_currency.lower()] -= amount
        user_data[target_currency.lower()] = user_data.get(target_currency.lower(), 0) + exchanged_rounded_amount

        # Сообщаем пользователю об успешном обмене
        await inter.response.send_message(f"Вы успешно обменяли {amount} {source_currency} на {exchanged_rounded_amount} {target_currency}.")

        # Сохраняем данные пользователя после обмена
        save_user_data(server_id, user_id, user_data)

# Слеш-команда для покупки майнера
@bot.slash_command(name='buy_miner', description="Команда для покупки майнера")
async def buy_miner_cmd(inter, miner: str):
    server_id, user_id = str(inter.guild_id), str(inter.user.id)
    miners_data = load_miners_data()
    user_data = load_user_data(server_id, user_id)
    
    if miner in miners_data:
        miner_info = miners_data[miner]
        if miner_info["price"] <= user_data.get("money", 0):
            user_data["money"] -= miner_info["price"]
            if "miners" not in user_data:
                user_data["miners"] = {}
            user_data["miners"][miner] = user_data["miners"].get(miner, 0) + 1
            save_user_data(server_id, user_id, user_data)
            await inter.response.send_message(f"Майнер {miner} успешно куплен!")
        else:
            await inter.response.send_message("У вас недостаточно средств для покупки этого майнера.")
    else:
        await inter.response.send_message("Данный майнер не существует.\n"
                                           "Используйте /miners_info для просмотра списка майнеров")

# Слеш-команда для просмотра информации о пользователе
@bot.slash_command(name='user_info', description="Просмотр информации о пользователе")
async def user_info_cmd(inter, user: disnake.User = None):
    server_id, user_id = str(inter.guild_id), str(inter.user.id)
    user_data = load_user_data(server_id, user_id)
    balance = user_data.get("money", 0)
    crypto_wallet = {key: value for key, value in user_data.items() if key in CRYPTO_LIST}
    
    balance_str = f'**Баланс:** {balance} :coin:'
    crypto_str = ""
    for currency, data in CRYPTO_LIST.items():
        amount = crypto_wallet.get(currency, 0)
        crypto_str += f'{data["emoji"]} {currency.capitalize()}: {amount}\n'
    if not crypto_str:
        crypto_str = "У вас нет криптовалют."
    miners_info = ""
    if "miners" in user_data:
        miners_info = "Майнеры:\n"
        for miner, count in user_data["miners"].items():
            miners_info += f"{miner} x{count}\n"
    business_info = ""
    if "business" in user_data:
        business_info = "Бизнесы:\n"
        for business, count in user_data["business"].items():
            business_info += f"{business}: {count}\n"
    if "apart" in user_data:
        apart_info = "Апартаменты:\n"
        for apart, count in user_data["apart"].items():
            apart_info += f"{apart}: {count}"
    
    await inter.response.send_message(f'Информация о пользователе {user_id}:\n\n{balance_str}\n\n{crypto_str}\n{miners_info}\n{business_info}\n{apart_info}')

# Загружаем данные майнеров
def load_miners_data():
    with open(MINERS_DATA_PATH, "r") as f:
        return json.load(f)

# Функция для получения информации о майнерах
def get_miners_info(miners_data):
    return "\n".join([f"{miner}: Цена - {miners_data[miner]['price']} :coin:, Хэшрейт - {miners_data[miner]['hashrate']}, Потребление - {miners_data[miner]['electricity_consumption']} :coin: в 5 минут, Поддерживаемые криптовалюты - {', '.join(miners_data[miner]['supported_cryptos'])}" for miner in miners_data])

# Функция для отправки длинного сообщения
async def send_long_message(channel, message_content):
    max_length = 2000
    for chunk in [message_content[i:i+max_length] for i in range(0, len(message_content), max_length)]:
        await channel.send(chunk)

# Слеш-команда для просмотра информации о майнерах
@bot.slash_command(name='miners_info', description="Просмотр информации о доступных майнерах")
async def miners_info_cmd(inter):
    miners_data = load_miners_data()
    miners_info = get_miners_info(miners_data)
    await inter.response.send_message("Доступные майнеры:\n")
    await send_long_message(inter.channel, miners_info)

@bot.slash_command(name='start_mining', description="Запуск майнинга")
async def start_mining_cmd(inter, selected_crypto: str = None):
    server_id, user_id = str(inter.guild_id), str(inter.user.id)
    user_data = load_user_data(server_id, user_id)

    if (server_id, user_id) in mining_tasks:
        await inter.response.send_message("Майнинг уже запущен.")
        return
    
    if selected_crypto is None and "miners" in user_data:
        supported_cryptos = set()
        for miner_name, miner_count in user_data["miners"].items():
            miner_info = load_miners_data()[miner_name]
            supported_cryptos.update(miner_info["supported_cryptos"])
        
        if len(supported_cryptos) > 1:
            await inter.response.send_message("Пожалуйста, выберите криптовалюту для майнинга: " + ', '.join(supported_cryptos))
            return
        elif len(supported_cryptos) == 1:
            selected_crypto = supported_cryptos.pop()

    if selected_crypto and selected_crypto.lower() not in CRYPTO_LIST:
        await inter.response.send_message("Выбранная криптовалюта не поддерживается.")
        return
    
    if "money" not in user_data or user_data["money"] < 0:
        await inter.response.send_message("Недостаточно средств для запуска майнинга.")
        return
    
    mining_tasks[(server_id, user_id)] = asyncio.create_task(mine_coins(server_id, user_id, selected_crypto))
    if "apart" in user_data:
        await inter.response.send_message("Майнинг успешно запущен!\n:bulb: У вас есть апартаменты, ваш доход умножен в 1,2 раза")
    else:
        await inter.response.send_message("Майнинг успешно запущен!\n:bulb: С апартаментами доход умножается в 1,2 раза")

async def mine_coins(server_id, user_id, selected_crypto=None):
    while True:
        await asyncio.sleep(300)
        user_data = load_user_data(server_id, user_id)
        if "miners" in user_data:
            for miner_name, miner_count in user_data["miners"].items():
                miner_info = load_miners_data()[miner_name]
                if selected_crypto not in miner_info["supported_cryptos"]:
                    continue

                hashrate = float(miner_info["hashrate"].split()[0]) * miner_count
                consumption = float(miner_info["electricity_consumption"].split()[0]) * miner_count
                coins_mined = 0
                if selected_crypto == "bitcoin":
                    coins_mined = hashrate / 5000
                elif selected_crypto == "ethereum":
                    coins_mined = hashrate / 20000
                elif selected_crypto == "bananacoin":
                    coins_mined = hashrate / 150
                if "apart" in user_data:
                    coins_mined *= 1.2

                user_data[selected_crypto] = user_data.get(selected_crypto, 0) + coins_mined
                user_data["money"] -= consumption
                save_user_data(server_id, user_id, user_data)
        else: 
            logger.debug("У пользователя отсутствуют майнеры, цикл продолжается")

@bot.slash_command(name='stop_mining', description="Остановка майнинга")
async def stop_mining_cmd(inter):
    server_id, user_id = str(inter.guild_id), str(inter.user.id)

    if (server_id, user_id) in mining_tasks:
        mining_task = mining_tasks[(server_id, user_id)]
        mining_task.cancel()
        del mining_tasks[(server_id, user_id)]
        await inter.response.send_message("Майнинг успешно остановлен!")
    else:
        await inter.response.send_message("Майнинг не запущен.")

# Загружаем данные бизнесов
def load_business_data():
    with open(BUSINESS_DATA_PATH, "r", encoding="UTF-8") as f:
        return json.load(f)

@bot.slash_command(name='buy_business', description="Купить бизнес")
async def buy_business(inter, business: str):
    server_id, user_id = str(inter.guild_id), str(inter.user.id)
    business_data = load_business_data()
    user_data = load_user_data(server_id, user_id)
    
    if business in business_data:
        business_info = business_data[business]
        if business_info["price"] <= user_data.get("money", 0):
            user_data["money"] -= business_info["price"]
            if "business" not in user_data:
                user_data["business"] = {}
            user_data["business"][business] = user_data["business"].get(business, 0) + 1
            save_user_data(server_id, user_id, user_data)
            await inter.response.send_message(f"Бизнес {business} успешно куплен!")
        else:
            await inter.response.send_message("У вас недостаточно средств для покупки этого бизнеса.")
    else:
        await inter.response.send_message("Данный бизнес не существует.\n"
                                           "Используйте /business_info для просмотра списка бизнесов")

# Функция для получения информации о бизнесах
def get_business_info(business_data, business):
    return f"{business}: Цена - {business_data[business]['price']} :coin:, Доход - {business_data[business]['income']}, Потребление - {business_data[business]['consumption']} :coin: в 30 минут"

# Слеш-команда для просмотра информации о бизнесах
@bot.slash_command(name='business_info', description="Просмотр информации о доступных бизнесах")
async def business_info(inter):
    business_data = load_business_data()
    await inter.response.send_message("Доступные бизнесы: \n")
    business_info = ""
    for business in business_data:
        business_info += get_business_info(business_data, business) + "\n"
    await send_long_message(inter.channel, business_info)

@bot.slash_command(name='sell_business', description="Продать бизнес")
async def sell_business(inter, business: str):
    server_id, user_id = str(inter.guild_id), str(inter.user.id)
    user_data = load_user_data(server_id, user_id)
    
    if "business" in user_data and business in user_data["business"]:
        business_data = load_business_data()
        if business in business_data:
            business_info = business_data[business]
            user_money = user_data.get("money", 0)
            user_business_count = user_data["business"][business]
            user_data["money"] = user_money + user_business_count * business_info["price"] * 0.8
            del user_data["business"][business]
            save_user_data(server_id, user_id, user_data)
            await inter.response.send_message(f"Бизнес {business} успешно продан!")
        else:
            await inter.response.send_message("Данный бизнес не существует.")
    else:
        await inter.response.send_message("У вас нет такого бизнеса.")

# Функция для обновления состояния бизнесов
async def update_businesses():
    while True:
        await asyncio.sleep(BUSINESS_COOLDOWN)
        business_data = load_business_data()
        all_user_data = load_all_user_data()
        for server_id, users_data in all_user_data.items():
            for user_id, user_data in users_data.items():
                if "business" in user_data:
                    user_businesses = user_data["business"]
                    for business_name, business_count in user_businesses.items():
                        if business_name in business_data:
                            business_info = business_data[business_name]
                            income = float(business_info["income"])
                            consumption = float(business_info["consumption"])
                            user_money = user_data.get("money", 0)
                            user_data["money"] = user_money + income * business_count - consumption * business_count
                            save_user_data(server_id, user_id, user_data)
                            logger.info(f"Обработан бизнес пользователя с айди: {user_id}")
                        else:
                            logger.info(f"Ошибка: Информация о бизнесе '{business_name}' не найдена.")

@bot.slash_command(name='work', description="Работать")
async def work_cmd(inter):
    # Выбираем случайную сложность примера
    difficulty = random.choice(['easy', 'medium', 'hard'])
    server_id, user_id = str(inter.guild_id), str(inter.user.id)
    user_data = load_user_data(server_id, user_id)

    # Генерируем пример в зависимости от сложности
    if difficulty == 'easy':
        num1 = random.randint(3, 15)
        num2 = random.randint(3, 15)
    elif difficulty == 'medium':
        num1 = random.randint(10, 80)
        num2 = random.randint(10, 80)
    else:
        num1 = random.randint(6, 50)
        num2 = random.randint(3, 70)

    # Выбираем случайный знак операции
    if difficulty == 'easy' or 'medium':
        operation = random.choice(['+', '-'])
    else:
        operation = random.choice(['*', '/'])

    # Вычисляем правильный ответ
    if operation == '+':
        correct_answer = num1 + num2
    elif operation == '-':
        correct_answer = num1 - num2
    elif operation == '*':
        correct_answer = num1 * num2
    else:
        # Проверка деления на 0
        if num2 == 0:
            num2 = 1
        correct_answer = num1 / num2

    # Отправляем пример пользователю
    await inter.response.send_message(f'Решите пример: {num1} {operation} {num2}')

    # Ожидаем ответ от пользователя
    try:
        user_answer = await bot.wait_for('message', check=lambda message: message.author == inter.author and message.channel == inter.channel, timeout=WORK_TIMEOUT)
        
        # Проверяем, что пользователь отправил не пустое сообщение
        if user_answer.content.strip() == "":
            await inter.followup.send("Ваше сообщение пустое, попробуйте снова.", ephemeral=True)
            return

        # Проверяем операцию и преобразуем ответ пользователя в число, если это не деление
        if operation != '/':
            user_answer = float(user_answer.content)
        else:
            # Преобразуем ответ пользователя в число с плавающей точкой
            user_answer = float(user_answer.content.replace(',', '.'))

        # Проверяем ответ пользователя
        if abs(user_answer - correct_answer) < 0.01:  # Учитываем погрешность из-за операций с плавающей точкой
            # Определяем количество монет в зависимости от сложности примера
            if difficulty == 'easy':
                reward = 25
            elif difficulty == 'medium':
                reward = 40
            else:
                reward = 80
            if 'apart' in user_data:
                reward *= 1.5
                # Добавляем монеты пользователю
                user_data = load_user_data(inter.guild.id, inter.author.id)
                user_data['money'] = user_data.get('money', 0) + reward
                save_user_data(inter.guild.id, inter.author.id, user_data)
                await inter.followup.send(f'Верно! Вы получаете {reward} монет.\n:bulb: Ваша награда умножена в 1,5 раза', ephemeral=True)
            else:
                # Добавляем монеты пользователю
                user_data = load_user_data(inter.guild.id, inter.author.id)
                user_data['money'] = user_data.get('money', 0) + reward
                save_user_data(inter.guild.id, inter.author.id, user_data)
                await inter.followup.send(f'Верно! Вы получаете {reward} монет.\n:bulb: С апартаментами награда умножается в 1,5 раза', ephemeral=True)
        else:
            await inter.followup.send('Неверно. Попробуйте еще раз.', ephemeral=True)
    except asyncio.TimeoutError:
        await inter.followup.send('Время вышло. Попробуйте снова.', ephemeral=True)

@bot.slash_command(name='bot_stats', description='Показывает статистику по боту')
async def bot_stats_cmd(inter: disnake.ApplicationCommandInteraction):
    await inter.response.defer()

    # Пинг
    latency = round(bot.latency * 1000)  # Пинг в миллисекундах

    # Аптайм
    current_time = time.time()
    uptime_seconds = int(current_time - START_TIME)
    uptime_str = time.strftime("%H:%M:%S", time.gmtime(uptime_seconds))

    # Информация о текущей гильдии
    guild = inter.guild
    server_id = inter.guild.id

    # Проверяем статус гильдии
    if server_id not in VERIFIED_GUILDS:
        guild_status = "Не верифицирована"
    else:
        guild_status = "Верифицирована"

    await inter.followup.send((
        f"Информация о боте:\n"
        f"Имя бота: {bot.user}\n"
        f"Имя гильдии: {guild.name}, Айди гильдии: {guild.id}, Участников: {guild.member_count}\n"
        f"Статус гильдии: {guild_status}\n"
        f"Пинг: {latency} ms\n"
        f"Аптайм: {uptime_str}"
    ))

@bot.slash_command(name='random_msg', description="Рандомное сообщение")
async def msg(inter):
    message = await randy_random()
    await inter.response.send_message(message)

# Загружаем данные апартаментов
def load_apart_data():
    with open(APART_DATA_PATH, "r", encoding="UTF-8") as f:
        return json.load(f)

@bot.slash_command(name='buy_apart', description="Купить апартаменты")
async def buy_business(inter, apart: str):
    server_id, user_id = str(inter.guild_id), str(inter.user.id)
    apart_data = load_apart_data()
    user_data = load_user_data(server_id, user_id)
    
    if apart in apart_data:
        apart_info = apart_data[apart]
        if apart_info["price"] <= user_data.get("money", 0):
            user_data["money"] -= apart_info["price"]
            if "apart" not in user_data:
                user_data["apart"] = {}
            user_data["apart"][apart] = user_data["apart"].get(apart, 0) + 1
            save_user_data(server_id, user_id, user_data)
            await inter.response.send_message(f"Апартаменты {apart} успешно куплены!")
        else:
            await inter.response.send_message("У вас недостаточно средств для покупки этих апартаментов.")
    else:
        await inter.response.send_message("Данные апартаменты не существуюn.\n"
                                           "Используйте /apart_info для просмотра списка апартаментов")

# Функция для получения информации о апатартаментах
def get_apart_info(apart_data, apart):
    return f"{apart}: Цена - {apart_data[apart]['price']} :coin:, Уровень - {apart_data[apart]['level']}, Налоги - {apart_data[apart]['taxes']} :coin: в час"

# Слеш-команда для просмотра информации о апартаментах
@bot.slash_command(name='apart_info', description="Просмотр информации о доступных апартаментах")
async def apart_info(inter):
    aparts_data = load_apart_data()
    await inter.response.send_message("Доступные апартаменты: \n")
    apart_info = ""
    for apart in aparts_data:
        apart_info += get_apart_info(aparts_data, apart) + "\n"
    await send_long_message(inter.channel, apart_info)

@bot.slash_command(name='sell_apart', description="Продать апартаменты")
async def sell_apart(inter, apart: str):
    server_id, user_id = str(inter.guild_id), str(inter.user.id)
    user_data = load_user_data(server_id, user_id)
    
    if "apart" in user_data and apart in user_data["apart"]:
        apart_data = load_apart_data()
        if apart in apart_data:
            apart_info = apart_data[apart]
            user_money = user_data.get("money", 0)
            user_apart_count = user_data["apart"][apart]
            user_data["money"] = user_money + user_apart_count * apart_info["price"] * 0.8
            del user_data["apart"][apart]
            save_user_data(server_id, user_id, user_data)
            await inter.response.send_message(f"Апартаменты {apart} успешно проданы!")
        else:
            await inter.response.send_message("Данные апартаменты не существуют.")
    else:
        await inter.response.send_message("У вас нет таких апартаментов.")

async def update_apart(): # Ворует у игроков деньги или апартаменты если денег нету
    while True:
        await asyncio.sleep(APART_COOLDOWN)
        apart_data = load_apart_data()
        all_user_data = load_all_user_data()
        for server_id, users_data in all_user_data.items():
            for user_id, user_data in users_data.items():
                if "apart" in user_data:
                    user_apart = user_data["apart"]
                    for apart_name, apart_count in list(user_apart.items()):
                        if apart_name in apart_data:
                            apart_info = apart_data[apart_name]
                            taxes = float(apart_info["taxes"])
                            user_money = user_data.get("money", 0)

                            total_taxes = taxes * apart_count
                            new_balance = user_money - total_taxes

                            if new_balance >= 0:
                                user_data["money"] = new_balance
                            else:
                                # Удаление апартаментов, если не хватает средств на налоги
                                del user_apart[apart_name]
                                logger.info(f"Пользователь с айди {user_id} потерял апартаменты '{apart_name}' из-за нехватки средств.")

                            save_user_data(server_id, user_id, user_data)
                            logger.debug(f"Обработаны апартаменты пользователя с айди: {user_id}")
                        else:
                            logger.warn(f"Ошибка: Информация о апартаментах '{apart_name}' не найдена.")
    
def get_token():
    token_directory = os.path.dirname(os.path.abspath(__file__))
    token_file_path = os.path.join(token_directory, "TOKEN.txt")
    if os.path.exists(token_file_path):
        try:
            with open(token_file_path, "r") as file:
                token = file.read().strip()
                if token:
                    return token
                else:
                    logger.error("Токен не найден в файле TOKEN.txt")
                    return None
        except Exception as e:
            logger.error(f"Ошибка при чтении токена из файла: {e}")
            return None
    else:
        logger.error("Файл TOKEN.txt не найден")
        TOKEN = input("Введите токен:")
        with open(token_file_path, 'w') as file:
            file.write(TOKEN)
        return TOKEN

def main():
    bot.last_work_time = {} 
    bot.last_steal_time = {}
    bot.loop.create_task(crypto_prices_generator()) # Запускаем генератор цен криптовалюты
    bot.loop.create_task(update_businesses()) # Запускаем проверку бизнесов
    bot.loop.create_task(update_apart()) # Запускаем проверку апартаментов (всем платить налоги!!!)
    bot.run(get_token())

if __name__ == "__main__":
    main()
