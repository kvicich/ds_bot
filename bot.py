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
BUSINESS_DATA_PATH = "business_data.json" # Файл с информацией о майнерах
under_construction = "working.txt"
mining_tasks = {}

logger = logging.getLogger('discord_bot')
logging.basicConfig(format='%(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# Создаем объект бота
intents = disnake.Intents.default()
bot = commands.Bot(command_prefix='!l!', sync_commands_debug=True, intents=intents)

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
            print("Была загружена дата пользователей")
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
    return all_user_data

# А вот эта штучка сохраняет дату юзеров
def save_user_data(server_id, user_id, data):
    ensure_server_data_dir(server_id)
    data_path = user_data_path(server_id, user_id)
    with open(data_path, "w", encoding="UTF-8") as f:
        json.dump(data, f)
        print("Была сохранена дата пользователей")

# Вычисляет точное местоположение личного файла юзера
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
    print(f"Бот запущен, его имя {bot.user}\n"
          f"Все сервера где есть бот: {bot.guilds}")
    await bot.change_presence(activity=disnake.Game(name="Как заебать юзера"))
    print("Статус бота изменён")

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

    # Проверка на использование промокода
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

        # Выполняем обмен
        exchanged_amount = amount * (source_rate / target_rate)
        exchanged_rounded_amount = round(exchanged_amount, 5)
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
    business_info = ""
    if "business" in user_data:
        business_info = "Бизнесы:\n"
        for business, count in user_data["business"].items():
            business_info += f"{business}: {count}\n"
    
    await inter.response.send_message(f'Информация о пользователе {user_id}:\n\n{balance_str}\n{crypto_str}\n{miners_info}\n{business_info}')

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
    return f"{business}: Цена - {business_data[business]['price']} :coin:, Доход - {business_data[business]['income']}, Потребление - {business_data[business]['consumption']} в 30 минут"

# Слеш-команда для просмотра информации о бизнесах
@bot.slash_command(name='business_info', description="Просмотр информации о доступных бизнесах")
async def business_info(inter):
    business_data = load_business_data()
    business_info = "Доступные майнеры:\n"
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
        await asyncio.sleep(1800)  # Указывать в секундах 60 секунд = 1 минута
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
                            print(f"Обработан бизнес пользователя с айди: {user_id}")
                        else:
                            print(f"Ошибка: Информация о бизнесе '{business_name}' не найдена.")

def load_works(server_id, user_id):
    data_path = "works.json"
    try:
        if os.path.exists(data_path):
            with open(data_path, "r", encoding="UTF-8") as f:
                print("Работы были загружены")
                return json.load(f)
        else:
            raise FileNotFoundError
    except FileNotFoundError:
        print("Отсутствуют работы, проверьте works.json")
        return None

@bot.slash_command(name='search_work', description="Поиск работы")
async def s_work_cmd(inter):
    # Загрузка данных пользователя
    user_id = inter.author.id
    user_data = load_user_data(inter.guild.id, user_id)

    # Проверка, была ли уже предложена работа пользователю
    if "current_work" in user_data:
        await inter.response.send_message("У вас уже есть работа. Увольтесь с этой работы, прежде чем искать новую.")
        return

    # Загрузка данных о работах
    works_data = load_works()

    # Поиск подходящей работы для пользователя
    suitable_work = None
    while not suitable_work:
        # Выбор случайной работы из загруженных данных
        random_work = random.choice(works_data)
        name = random_work["name"]
        work_type = random_work["type"]
        difficulty = random_work["difficulty"]

        # Проверка критериев пользователя
        if check_criteria(user_data, work_type, difficulty):
            suitable_work = random_work

    # Сохранение предложенной работы в данных пользователя
    user_data["current_work"] = suitable_work
    save_user_data(inter.guild.id, user_id, user_data)

    # Отправка информации о предложенной работе пользователю
    description = suitable_work["description"]
    salary = suitable_work["salary"]
    message_content = f"Вам предлагается работа: {name}\nОписание: {description}\nТип: {work_type}\nСложность: {difficulty}\nЗаработок: {salary}"
    message_content += "\n\nПринять предложенную работу? (Нажмите 👍 чтобы принять, 👎 чтобы отклонить)"

    # Отправка сообщения с предложением
    message = await inter.response.send_message(message_content)

    # Ожидание реакции от пользователя
    await message.add_reaction("👍")
    await message.add_reaction("👎")

    # Функция для проверки реакции пользователя
    def check_reaction(reaction, user):
        return user == inter.author and str(reaction.emoji) in ["👍", "👎"]

    try:
        reaction, _ = await bot.wait_for("reaction_add", timeout=30.0, check=check_reaction)
        if str(reaction.emoji) == "👍":
            await inter.followup.send(content="Пожалуйста, не закрывайте модальное окно! 👍", ephemeral=True)
        elif str(reaction.emoji) == "👎":
            await inter.response.send_message("Вы отклонили предложенную работу. 👎")
        else:
            await inter.response.send_message("Неверная реакция. Предложение отменено.")
    except asyncio.TimeoutError:
        await inter.response.send_message("Время ожидания истекло. Предложение отменено.")

# Функция для проверки критериев пользователя
def check_criteria(user_data, work_type, difficulty):
    # В данном примере просто возвращаем True
    return True

@bot.slash_command(name='work', description="Работать")
async def w_work_cmd(inter):
    message = await randy_random()
    await inter.response.send_message(message)

@bot.slash_command(name='quit_work', description="Уволится с работы")
async def q_work_cmd(inter):
    # Загрузка данных пользователя
    user_id = inter.author.id
    user_data = load_user_data(inter.guild.id, user_id)

    # Проверка, есть ли у пользователя предложенная работа
    if "current_work" not in user_data:
        await inter.response.send_message("У вас нет предложенной работы.")
        return

    # Получение информации о текущей работе пользователя
    current_work = user_data["current_work"]
    name = current_work["name"]

    # Предложение пользователю уйти с работы
    message_content = f"Хотите уволиться с работы '{name}'? (Нажмите 👍 чтобы подтвердить, 👎 чтобы отклонить)"
    message = await inter.response.send_message(message_content)

    # Ожидание реакции от пользователя
    await message.add_reaction("👍")
    await message.add_reaction("👎")

    # Функция для проверки реакции пользователя
    def check_reaction(reaction, user):
        return user == inter.author and str(reaction.emoji) in ["👍", "👎"]

    try:
        reaction, _ = await bot.wait_for("reaction_add", timeout=30.0, check=check_reaction)
        if str(reaction.emoji) == "👍":
            # Удаление информации о текущей работе у пользователя
            del user_data["current_work"]
            save_user_data(inter.guild.id, user_id, user_data)
            await inter.response.send_message("Вы уволились с работы. 👍")
        elif str(reaction.emoji) == "👎":
            await inter.response.send_message("Отказ от работы отменён. 👎")
        else:
            await inter.response.send_message("Неверная реакция. Отказ от работы отменён.")
    except asyncio.TimeoutError:
        await inter.response.send_message("Время ожидания истекло. Отказ от работы отменён. 👎")

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
    bot.run(get_token())

if __name__ == "__main__":
    main()
