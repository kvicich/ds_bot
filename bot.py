import os
import json
import disnake
from disnake.ext import commands
import logging
import random
import time
import asyncio

# Переменные
SERVERS_DATA_DIR = "servers_data"  # Папка с данными серверов
WORK_COOLDOWN = 250 # Время в секундах между попытками зароботка
STEAL_COOLDOWN = 500  # Время в секундах между попытками кражи
FAILED_STEAL_MIN_LOSS = 15 # Минимальная потеря монет в /steal
FAILED_STEAL_MAX_LOSS = 350 # Максимальная потеря монет в /steal
MINERS_DATA_PATH = "miners_data.json" # Файл с датой майнеров
under_construction = "working.txt"
mining_tasks = {}

logger = logging.getLogger('discord_bot')
logging.basicConfig(format='%(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# Создаем объект бота
intents = disnake.Intents.default()
bot = commands.Bot(command_prefix='!l!', sync_commands_debug=True, intents=intents)

# Проверяем наличие папки сервера и создаём ее, если она отсутствует
def ensure_server_data_dir(server_id):
    server_dir = os.path.join(SERVERS_DATA_DIR, str(server_id))
    if not os.path.exists(server_dir):
        os.makedirs(server_dir)

# Штучка, дату юзеров загружать
def load_user_data(server_id, user_id):
    ensure_server_data_dir(server_id)
    data_path = user_data_path(server_id, user_id)
    if os.path.exists(data_path):
        with open(data_path, "r") as f:
            print("Была загружена дата пользователей")
            return json.load(f)
    else:
        with open(data_path, "w") as f:
            json.dump({}, f)
            print("Была загружена дата пользователей")
        return {}

# А вот эта штучка сохраняет дату юзеров
def save_user_data(server_id, user_id, data):
    ensure_server_data_dir(server_id)
    data_path = user_data_path(server_id, user_id)
    with open(data_path, "w") as f:
        json.dump(data, f)
        print("Была сохранена дата пользователей")

def user_data_path(server_id, user_id):
    return os.path.join(SERVERS_DATA_DIR, str(server_id), f"{user_id}.json")

# Декоратор для проверки, является ли пользователь администратором
def isAdmin(ctx):
    admin_data_path = os.path.join("admins.json")
    if os.path.exists(admin_data_path):
        with open(admin_data_path, "r") as file:
            admins = json.load(file)
            return ctx.author.id in admins
    return False

# Декоратор для команд, доступных только администраторам
def admin_command(command):
    async def wrapper(ctx, *args, **kwargs):
        if isAdmin(ctx):
            await command(ctx, *args, **kwargs)
        else:
            await ctx.send("У вас нет прав для выполнения этой команды.")
    return wrapper

# Декоратор для проверки, является ли пользователь администратором
def isTester(ctx):
    admin_data_path = os.path.join("Testers.json")
    if os.path.exists(admin_data_path):
        with open(admin_data_path, "r") as file:
            admins = json.load(file)
            return ctx.author.id in admins
    return False

# Декоратор для команд, доступных только администраторам
def Tester_command(command):
    async def wrapper(ctx, *args, **kwargs):
        if isTester(ctx):
            await command(ctx, *args, **kwargs)
        else:
            await ctx.send("У вас нет прав для выполнения этой команды.")
    return wrapper

# Декоратор для проверки, является ли пользователь администратором
def isOwner(ctx):
    admin_data_path = os.path.join("Owner.json")
    if os.path.exists(admin_data_path):
        with open(admin_data_path, "r") as file:
            admins = json.load(file)
            return ctx.author.id in admins
    return False

# Декоратор для команд, доступных только администраторам
def owner_command(command):
    async def wrapper(ctx, *args, **kwargs):
        if isOwner(ctx):
            await command(ctx, *args, **kwargs)
        else:
            await ctx.send("У вас нет прав для выполнения этой команды.")
    return wrapper

# Асинхронная функция для генерации случайного сообщения
async def randy_random():
    with open(under_construction, "r", encoding='utf-8') as file:
        messages = file.readlines()
        message = random.choice(messages).strip()
        return message

# Команда для добавления тестера
@owner_command
@bot.slash_command(name='add_tester', description="Добавляет тестера в бот.")
async def add_tester(ctx, member: disnake.User):
    admin_data_path = os.path.join("Testers.json")

    if os.path.exists(admin_data_path):
        with open(admin_data_path, "r") as file:
            admins = json.load(file)
    else:
        admins = []

    admins.append(member.id)

    with open(admin_data_path, "w") as file:
        json.dump(admins, file)

    await ctx.send(f"{member.mention} добавлен в список тестеров.")

# Команда для удаления тестера
@owner_command
@bot.slash_command(name='rem_tester', description="Удаляет тестера с бота.")
async def rem_tester(ctx, member: disnake.User):
    admin_data_path = os.path.join("Testers.json")

    if os.path.exists(admin_data_path):
        with open(admin_data_path, "r") as file:
            admins = json.load(file)
        if member.id in admins:
            admins.remove(member.id)
            with open(admin_data_path, "w") as file:
                json.dump(admins, file)
            await ctx.send(f"{member.mention} удален из списка тестеров.")
        else:
            await ctx.send(f"{member.mention} не является тестером.")
    else:
        await ctx.send("На сервере нет тестеров.")

# Событие выполняющееся после полного запуска бота
@bot.event
async def on_ready():
    print(f"Бот запущен, его имя {bot.user}")

# Стартовая команда
@bot.slash_command(name='start', description="Стартовая команда.")
async def start_cmd(inter):
    user_name = inter.user.name
    guild_name = inter.guild.name
    await inter.response.send_message(f'Приветствую, это на данный момент тестовая команда. Все команды: /help Имя бота: {bot.user.name}. Твой юзернейм: {user_name}. Имя сервера: {guild_name}. Тестовое эмодзи: :fly: ')

# Команда для подработки
@bot.slash_command(name='sidejob', description="Работка.")
async def SideJob_cmd(inter):
    user_id = str(inter.user.id)
    server_id = str(inter.guild_id)
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
    currency_earned = random.randint(20, 143)
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
    user_id = str(inter.user.id)
    server_id = str(inter.guild_id)
    current_time = time.time()
    last_steal_time = bot.last_steal_time.get(server_id, {})
    if user_id in last_steal_time:
        time_elapsed = current_time - last_steal_time[user_id]
        if time_elapsed < STEAL_COOLDOWN:
            time_left = STEAL_COOLDOWN - time_elapsed
            await inter.response.send_message(f'Вы недавно уже пытались что-то украсть. Подождите еще {int(time_left)} секунд.')
            return
    await inter.response.defer()  # Отправляем ответ о том, что команда получена и будет обработана
    last_steal_time[user_id] = current_time
    bot.last_steal_time[server_id] = last_steal_time
    if random.random() < 0.4567:  # Шанс 45,67%
        stolen_amount = random.randint(40, 334)
        with open("steal_message.txt", "r", encoding="utf-8") as file:
            messages = file.readlines()
            steal_message = random.choice(messages).strip()
        user_data = load_user_data(server_id, user_id)
        user_balance = user_data.get("money", 0)
        user_balance += stolen_amount
        user_data["money"] = user_balance
        save_user_data(server_id, user_id, user_data)
        steal_message = steal_message.replace("{stolen_amount}", str(stolen_amount))
        await inter.edit_original_message(content=f'{inter.author.mention}, {steal_message}')
    else:
        lost_amount = random.randint(FAILED_STEAL_MIN_LOSS, FAILED_STEAL_MAX_LOSS)
        user_data = load_user_data(server_id, user_id)
        user_balance = user_data.get("money", 0)
        user_balance -= lost_amount  
        user_data["money"] = user_balance
        save_user_data(server_id, user_id, user_data)
        
@bot.slash_command(name='ping', description="Проверяет ваш пинг.")
async def ping(inter):
    start_time = time.time()
    # Делаем фиктивный запрос, чтобы измерить задержку
    await inter.response.defer()
    end_time = time.time()
    ping_time = round((end_time - start_time) * 1000)
    await inter.edit_original_message(content=f"Понг!\n"
                                      f"Ваш пинг: {ping_time} мс"
    )

# Команда для добавления администратора
@bot.slash_command(name='add_admin', description="Добавляет администратора на сервере.")
@owner_command
async def add_admin(ctx, member: disnake.Member):
    admin_data_path = os.path.join("admins.json")

    if os.path.exists(admin_data_path):
        with open(admin_data_path, "r") as file:
            admins = json.load(file)
    else:
        admins = []

    admins.append(member.id)

    with open(admin_data_path, "w") as file:
        json.dump(admins, file)

    await ctx.send(f"{member.mention} добавлен в список администраторов.")

# Команда для удаления администратора
@bot.slash_command(name='rem_admin', description="Удаляет администратора с сервера.")
@owner_command
async def rem_admin(ctx, member: disnake.Member):
    admin_data_path = os.path.join("admins.json")

    if os.path.exists(admin_data_path):
        with open(admin_data_path, "r") as file:
            admins = json.load(file)
        if member.id in admins:
            admins.remove(member.id)
            with open(admin_data_path, "w") as file:
                json.dump(admins, file)
            await ctx.send(f"{member.mention} удален из списка администраторов.")
        else:
            await ctx.send(f"{member.mention} не является администратором.")
    else:
        await ctx.send("На сервере нет администраторов.")

# Команда для просмотра текущих курсов криптовалют
@bot.slash_command(name='crypto_prices', description='Просмотреть текущие курсы криптовалют.')
async def crypto_prices_cmd(ctx):
    crypto_list = load_crypto_prices()
    prices_str = '\n'.join([f"{crypto_list[currency]['emoji']} {currency.capitalize()}: {crypto_list[currency]['price']} :coin:" for currency in crypto_list])
    await ctx.send(f"Текущие курсы криптовалют:\n{prices_str}")

# Функция для генерации новых цен криптовалют
def generate_crypto_prices():
    crypto_list = load_crypto_prices()
    for currency in crypto_list:
        change1 = random.uniform(-1.9, -0.1)
        change2 = random.uniform(0.1, 1.9)
        change_percent = random.uniform(change1, change2)  # Изменение на случайный процент от -1% до 1%
        if random.random() < 0.05:  # Шанс 5% на редкое изменение
            change1 = random.uniform(0.6, 0.9)
            change2 = random.uniform(1.01, 1.3)
            change_percent *= random.uniform(change1, change2)  # Редкое изменение от -20% до 20%
        crypto_list[currency]['price'] *= (1 + change_percent / 100)  # Применяем изменение
        # Округляем цены криптовалют до нуля знаков после запятой/точки
        crypto_list[currency]['price'] = round(crypto_list[currency]['price'], 0)
    with open("crypto_prices.json", "w") as file:
        json.dump(crypto_list, file)
    print("Изменились цены криптовалют!")

# Цикл меняющий цены раз в 5 минут
async def crypto_prices_generator():
    while True:
        await asyncio.sleep(300)  # Пауза в 5 минут
        generate_crypto_prices()

# Функция для сохранения текущих курсов криптовалют
def save_crypto_prices(crypto_list):
    with open("crypto_prices.json", "w") as file:
        json.dump(crypto_list, file)
        print("Сохранены курсы криптовалют!")

# Функция для загрузки текущих курсов криптовалют из файла
def load_crypto_prices():
    if os.path.exists("crypto_prices.json"):
        with open("crypto_prices.json", "r") as file:
            print("Загружены курсы криптовалют!")
            return json.load(file)
    else:
        print("Загружены начальные курсы криптовалют! Проверьте файл crypto_prices.json!")
        return {"bitcoin": {"emoji": ":dvd:", "price": 50000}, "ethereum": {"emoji": ":cd:", "price": 10000}, "bananacoin": {"emoji": ":banana:", "price": 250}}

CRYPTO_LIST = load_crypto_prices()

@admin_command
@bot.slash_command(name="change_crypto_prices", description='Сменить цены криптовалют.')
async def change_crypto_prices(inter):
    print("Кто-то принудительно изменил цены криптовалют!")
    generate_crypto_prices()
    await inter.response.send_message("Вы принудительно изменили цены криптовалют!")

# Команда для выдачи денег
@admin_command
@bot.slash_command(name='give_money', description="Выдает деньги пользователю.")
async def give_money(inter, member: disnake.Member, amount: int):

    # Загрузка данных пользователя
    user_id = str(inter.author.id)
    server_id = str(inter.guild.id)
    user_data = load_user_data(server_id, user_id)

    # Добавление денег пользователю
    user_data['money'] = user_data.get('money', 0) + amount

    # Отправка сообщения о выдаче денег
    await inter.response.send_message(f'Пользователь {member.mention} (ID: {member.id}) получил {amount} денег.')

    # Сохранение данных пользователя после выдачи денег
    save_user_data(server_id, user_id, user_data)

# Команда для отнятия денег
@admin_command
@bot.slash_command(name='take_money', description="Отнимает деньги у пользователя.")
async def take_money(inter, member: disnake.Member, amount: int):

    # Загрузка данных пользователя
    user_id = str(member.id)
    server_id = str(inter.guild.id)
    user_data = load_user_data(server_id, user_id)

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
@admin_command
@bot.slash_command(name='give_crypto', description="Выдает криптовалюту пользователю.")
async def give_crypto(inter, currency: str, member: disnake.Member, amount: int):

    # Проверка наличия указанной криптовалюты в списке
    if currency.lower() not in CRYPTO_LIST:
        await inter.response.send_message(f'Криптовалюта {currency} не найдена в списке доступных криптовалют.')
        return

    # Загрузка данных пользователя
    user_id = str(inter.author.id)
    server_id = str(inter.guild.id)
    user_data = load_user_data(server_id, user_id)

    # Добавление указанной криптовалюты пользователю
    user_data[currency.lower()] = user_data.get(currency.lower(), 0) + amount

    # Отправка сообщения о выдаче криптовалюты
    await inter.response.send_message(f'Пользователь {member.mention} (ID: {member.id}) получил {amount} {currency}.')

    # Сохранение данных пользователя после выдачи криптовалюты
    save_user_data(server_id, user_id, user_data)

# Команда для отнятия криптовалюты
@admin_command
@bot.slash_command(name='take_crypto', description="Отнимает криптовалюту у пользователя.")
async def take_crypto(inter, currency: str, member: disnake.Member, amount: int):

    # Проверка наличия указанной криптовалюты в списке
    if currency.lower() not in CRYPTO_LIST:
        await inter.response.send_message(f'Криптовалюта {currency} не найдена в списке доступных криптовалют.')
        return

    # Загрузка данных пользователя
    user_id = str(member.id)
    server_id = str(inter.guild.id)
    user_data = load_user_data(server_id, user_id)

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
async def promo(ctx, code: str):
    server_id = str(ctx.guild.id)
    user_id = str(ctx.author.id)
    user_data = load_user_data(server_id, user_id)
    used_promocodes = user_data.get('used_promocodes', [])
    promo_codes = load_promo_codes()  

    if code in used_promocodes:
        await ctx.send("Промокод уже использован.")
        return

    if code in promo_codes:
        action = promo_codes[code]
        try:
            value, key = action.split(' =+ ')
        except ValueError:
            await ctx.send("Неправильный формат действия промокода.")
            return

        if key == 'money':
            user_data['money'] = user_data.get('money', 0) + float(value)
            await ctx.send(f"Вы получили {value} денег.")
        elif key in ['bitcoin', 'ethereum', 'bananacoin']:
            user_data[key] = user_data.get(key, 0) + float(value)
            await ctx.send(f"Вы получили {value} {key}.")
        else:
            await ctx.send("Произошла ошибка при обработке промокода.")

        used_promocodes.append(code)
        user_data['used_promocodes'] = used_promocodes
    else:
        await ctx.send("Промокод не найден.")

    save_user_data(server_id, user_id, user_data)
    
@bot.slash_command(name="exchange", description='Позволяет обменивать валюты')
async def exchange_cmd(ctx, source_currency: str, target_currency: str, amount: float):
    # Проверяем, что валюты из списка доступных
    if source_currency.lower() not in CRYPTO_LIST and source_currency.lower() != "money":
        await ctx.send(f"Валюта {source_currency} не найдена в списке доступных криптовалют и денег.")
        return
    if target_currency.lower() not in CRYPTO_LIST and target_currency.lower() != "money":
        await ctx.send(f"Валюта {target_currency} не найдена в списке доступных криптовалют и денег.")
        return

    # Обрабатываем случай обмена денег на криптовалюту
    if source_currency.lower() == "money":
        # Проверяем, что пользователь имеет достаточно денег для обмена
        user_id = str(ctx.author.id)
        server_id = str(ctx.guild.id)
        user_data = load_user_data(server_id, user_id)
        if user_data.get("money", 0) < amount:
            await ctx.send("У вас недостаточно денег для обмена.")
            return

        # Вычисляем сумму после обмена
        target_rate = CRYPTO_LIST[target_currency.lower()]["price"]
        exchanged_amount = amount / target_rate
        exchanged_rounded_amount = round(exchanged_amount, 6)

        # Выполняем обмен
        user_data["money"] -= amount
        user_data[target_currency.lower()] = user_data.get(target_currency.lower(), 0) + exchanged_rounded_amount

        # Сообщаем пользователю об успешном обмене
        await ctx.send(f"Вы успешно обменяли {amount} денег на {exchanged_rounded_amount} {target_currency}.")

        # Сохраняем данные пользователя после обмена
        save_user_data(server_id, user_id, user_data)
    
    # Обрабатываем случай обмена криптовалюты на деньги
    elif target_currency.lower() == "money":
        # Проверяем, что пользователь имеет достаточно криптовалюты для обмена
        user_id = str(ctx.author.id)
        server_id = str(ctx.guild.id)
        user_data = load_user_data(server_id, user_id)
        if user_data.get(source_currency.lower(), 0) < amount:
            await ctx.send(f"У вас недостаточно {source_currency} для обмена.")
            return

        # Вычисляем сумму после обмена
        source_rate = CRYPTO_LIST[source_currency.lower()]["price"]
        exchanged_amount = amount * source_rate
        exchanged_rounded_amount = round(exchanged_amount, 5)

        # Выполняем обмен
        user_data["money"] = user_data.get("money", 0) + exchanged_rounded_amount
        user_data[source_currency.lower()] -= amount

        # Сообщаем пользователю об успешном обмене
        await ctx.send(f"Вы успешно обменяли {amount} {source_currency} на {exchanged_rounded_amount} денег.")

        # Сохраняем данные пользователя после обмена
        save_user_data(server_id, user_id, user_data)
    
    # Обрабатываем обмен криптовалюты на криптовалюту
    else:
        # Получаем текущие курсы валют из списка
        source_rate = CRYPTO_LIST[source_currency.lower()]["price"]
        target_rate = CRYPTO_LIST[target_currency.lower()]["price"]

        # Проверяем, что пользователь имеет достаточно криптовалюты для обмена
        user_id = str(ctx.author.id)
        server_id = str(ctx.guild.id)
        user_data = load_user_data(server_id, user_id)
        if user_data.get(source_currency.lower(), 0) < amount:
            await ctx.send(f"У вас недостаточно {source_currency} для обмена.")
            return

        # Вычисляем сумму после обмена
        exchanged_amount = amount * (source_rate / target_rate)
        exchanged_rounded_amount = round(exchanged_amount, 5)

        # Выполняем обмен
        user_data[source_currency.lower()] -= amount
        user_data[target_currency.lower()] = user_data.get(target_currency.lower(), 0) + exchanged_rounded_amount

        # Сообщаем пользователю об успешном обмене
        await ctx.send(f"Вы успешно обменяли {amount} {source_currency} на {exchanged_rounded_amount} {target_currency}.")

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
    user_id = str(user.id) if user else str(inter.user.id)
    server_id = str(inter.guild_id)
    
    user_data = load_user_data(server_id, user_id)
    balance = user_data.get("money", 0)
    crypto_wallet = {key: value for key, value in user_data.items() if key in CRYPTO_LIST}
    
    balance_str = f'**Баланс:** {balance} :coin:\n\n'
    
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
    
    await inter.response.send_message(f'Информация о пользователе {user_id}:\n\n{balance_str}{crypto_str}\n{miners_info}')

# Загружаем данные майнеров
def load_miners_data():
    with open(MINERS_DATA_PATH, "r") as f:
        return json.load(f)

# Функция для получения информации о майнерах
def get_miners_info(miners_data):
    return "\n".join([f"{miner}: Цена - {miners_data[miner]['price']} :coin:, Хэшрейт - {miners_data[miner]['hashrate']}, Потребление - {miners_data[miner]['electricity_consumption']} в 5 минут, Поддерживаемые криптовалюты - {', '.join(miners_data[miner]['supported_cryptos'])}" for miner in miners_data])

# Функция для отправки длинного сообщения
async def send_long_message(channel, message_content):
    max_length = 2000
    for chunk in [message_content[i:i+max_length] for i in range(0, len(message_content), max_length)]:
        await channel.send(chunk)

# Слеш-команда для просмотра информации о майнерах
@bot.slash_command(name='miners_info', description="Просмотр информации о доступных майнерах")
async def miners_info_cmd(inter):
    miners_data = load_miners_data()
    miners_info = "Доступные майнеры:\n" + get_miners_info(miners_data)
    await send_long_message(inter.channel, miners_info)

@bot.slash_command(name='start_mining', description="Запуск майнинга")
async def start_mining_cmd(inter, selected_crypto: str = None):
    server_id = str(inter.guild_id)
    user_id = str(inter.user.id)
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
    await inter.response.send_message("Майнинг успешно запущен!")

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

                user_data[selected_crypto] = user_data.get(selected_crypto, 0) + coins_mined
                user_data["money"] -= consumption
                save_user_data(server_id, user_id, user_data)
        else: 
            print("У пользователя отсутствуют майнеры, цикл продолжается")

@bot.slash_command(name='stop_mining', description="Остановка майнинга")
async def stop_mining_cmd(inter):
    server_id = str(inter.guild_id)
    user_id = str(inter.user.id)
    
    if (server_id, user_id) in mining_tasks:
        mining_task = mining_tasks[(server_id, user_id)]
        mining_task.cancel()
        del mining_tasks[(server_id, user_id)]
        await inter.response.send_message("Майнинг успешно остановлен!")
    else:
        await inter.response.send_message("Майнинг не запущен.")

@bot.slash_command(name='buy_business', description="Купить бизнес")
async def buy_business(inter):
    random_message = await randy_random()
    await inter.response.send_message(random_message)

@bot.slash_command(name='businnes_control', description="Управлять бизнесами")
async def business_control(inter):
    random_message = await randy_random()
    await inter.response.send_message(random_message)

@bot.slash_command(name='sell_business', description="Продать бизнес")
async def sell_business(inter):
    random_message = await randy_random()
    await inter.response.send_message(random_message)

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
        return None

def main():
    bot.last_work_time = {}
    bot.last_steal_time = {}
    bot.loop.create_task(crypto_prices_generator())
    bot.run(get_token())

if __name__ == "__main__":
    main()
