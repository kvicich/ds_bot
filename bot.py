import os
import json
import discord
from discord.ext import commands
import logging
import random
import time
import asyncio

# Переменные
SERVERS_DATA_DIR = "servers_data"  # Папка с данными серверов
WORK_COOLDOWN = 1 # Время в секундах между попытками зароботка
STEAL_COOLDOWN = 5  # Время в секундах между попытками кражи
FAILED_STEAL_MIN_LOSS = 1 # Минимальная потеря монет
ADMIN_DATA_DIR = "servers_data"
FAILED_STEAL_MAX_LOSS = 350 # Максимальная потеря монет
BASE_JOIN_SAMPLE_FILE = "base-join-sample.txt" # Тут хранится базовый пример
CRYPTO_LIST = {
    'bitcoin': {'emoji': ':dvd:', 'price': random.randint(50000, 55000)},
    'ethereum': {'emoji': ':cd:', 'price': random.randint(10000, 15000)},
    'bananacoin': {'emoji': ':banana:', 'price': random.randint(13, 250)}
}

logger = logging.getLogger('discord_bot')
intents = discord.Intents.default()
intents.messages = True

logging.basicConfig(format='%(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

bot = commands.Bot(command_prefix='/', intents=intents)

# Проверка наличия папки сервера и создание ее, если она отсутствует
def ensure_server_data_dir(server_id):
    server_dir = os.path.join(SERVERS_DATA_DIR, str(server_id))
    if not os.path.exists(server_dir):
        os.makedirs(server_dir)

# В функции load_user_data
def load_user_data(server_id, user_id):
    ensure_server_data_dir(server_id)
    data_path = user_data_path(server_id, user_id)
    if os.path.exists(data_path):
        with open(data_path, "r") as f:
            return json.load(f)
    else:
        with open(data_path, "w") as f:
            json.dump({}, f)
        return {}

# В функции save_user_data
def save_user_data(server_id, user_id, data):
    ensure_server_data_dir(server_id)
    data_path = user_data_path(server_id, user_id)
    with open(data_path, "w") as f:
        json.dump(data, f)

# В функции file_checker
def file_checker(file_path, server_id):
    ensure_server_data_dir(server_id)
    server_dir = os.path.join(SERVERS_DATA_DIR, str(server_id))
    if not os.path.exists(server_dir):
        os.makedirs(server_dir)
        print(f"Папка для сервера с ID {server_id} была создана.")

    file_name = os.path.basename(file_path)
    file_path = os.path.join(server_dir, file_name)

    if not os.path.exists(file_path):
        with open(file_path, 'w'):
            pass
        print(f"Файл {file_name} для сервера с ID {server_id} был создан.")
    else:
        print(f"Файл {file_name} для сервера с ID {server_id} уже существует.")

def user_data_path(server_id, user_id):
    return os.path.join(SERVERS_DATA_DIR, str(server_id), f"{user_id}.json")

# Декоратор для проверки, является ли пользователь администратором
def isAdmin(ctx):
    admin_data_path = os.path.join(ADMIN_DATA_DIR, str(ctx.guild.id), "admins.json")
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

@bot.event
async def on_ready():
    print(f"Бот запущен, его имя {bot.user.name}")

@bot.command(name='start')
async def start_cmd(ctx):
    user_name = ctx.author.name
    guild_name = ctx.guild.name
    await ctx.send(f'Приветствую, это на данный момент тестовая команда. Все команды: /help Имя бота: {bot.user.name}. Твой юзернейм: {user_name}. Имя сервера: {guild_name}. Тестовое эмодзи: :fly: ')

@bot.command(name='SideJob')
async def SideJob_cmd(ctx):
    user_id = str(ctx.author.id)
    server_id = str(ctx.guild.id)
    current_time = time.time()
    last_work_time = bot.last_work_time.get(server_id, {})
    if user_id in last_work_time:
        time_elapsed = current_time - last_work_time[user_id]
        if time_elapsed < WORK_COOLDOWN:
            time_left = WORK_COOLDOWN - time_elapsed
            await ctx.send(f'{ctx.author.mention}, вы уже работали недавно. Подождите еще {int(time_left)} секунд.')
            return
    last_work_time[user_id] = current_time
    bot.last_work_time[server_id] = last_work_time

    currency_earned = random.randint(15, 135)

    with open("work_message.txt", "r", encoding="utf-8") as file:
        messages = file.readlines()
        work_message = random.choice(messages).strip()

    user_data = load_user_data(server_id, user_id)
    user_balance = user_data.get("balance", 0)
    user_balance += currency_earned
    user_data["balance"] = user_balance
    save_user_data(server_id, user_id, user_data)

    work_message = work_message.replace("{currency_earned}", str(currency_earned))
    
    await ctx.send(f'{ctx.author.mention}, {work_message}.')

# Команда для просмотра текущего баланса и криптовалют
@bot.command(name='balance')
async def balance_cmd(ctx):
    user_id = str(ctx.author.id)
    server_id = str(ctx.guild.id)
    user_data = load_user_data(server_id, user_id)
    
    balance = user_data.get("balance", 0)
    crypto_wallet = user_data.get("crypto_wallet", {})
    
    balance_str = f'**Баланс:** {balance} :coin:\n\n'
    crypto_str = '\n'.join([f'{CRYPTO_LIST[currency]["emoji"]} {currency.capitalize()}: {amount}' for currency, amount in crypto_wallet.items()])
    
    await ctx.send(f'{ctx.author.mention}, ваш текущий баланс и криптовалюты:\n\n{balance_str}{crypto_str}')

@bot.command(name='steal')
async def steal_cmd(ctx):
    user_id = str(ctx.author.id)
    server_id = str(ctx.guild.id)
    current_time = time.time()
    last_steal_time = bot.last_steal_time.get(server_id, {})
    if user_id in last_steal_time:
        time_elapsed = current_time - last_steal_time[user_id]
        if time_elapsed < STEAL_COOLDOWN:
            time_left = STEAL_COOLDOWN - time_elapsed
            await ctx.send(f'{ctx.author.mention}, вы недавно уже пытались что-то украсть. Подождите еще {int(time_left)} секунд.')
            return
    last_steal_time[user_id] = current_time
    bot.last_steal_time[server_id] = last_steal_time

    if random.random() < 0.5:  # Шанс 50%
        stolen_amount = random.randint(20, 265)
        with open("steal_message.txt", "r", encoding="utf-8") as file:
            messages = file.readlines()
            steal_message = random.choice(messages).strip()

        user_data = load_user_data(server_id, user_id)
        user_balance = user_data.get("balance", 0)
        user_balance += stolen_amount
        user_data["balance"] = user_balance
        save_user_data(server_id, user_id, user_data)

        steal_message = steal_message.replace("{stolen_amount}", str(stolen_amount))
        await ctx.send(f'{ctx.author.mention}, {steal_message}')
    else:
        lost_amount = random.randint(FAILED_STEAL_MIN_LOSS, FAILED_STEAL_MAX_LOSS)
        user_data = load_user_data(server_id, user_id)
        user_balance = user_data.get("balance", 0)
        user_balance = max(0, user_balance - lost_amount)  # Не позволяйте отрицательный баланс
        user_data["balance"] = user_balance
        save_user_data(server_id, user_id, user_data)

        await ctx.send(f'{ctx.author.mention}, попытка украсть провалилась! Вы потеряли {lost_amount} монет.')

@bot.event
async def on_error(event, *args, **kwargs):
    logger.error(f"Произошла ошибка в событии {event}", exc_info=True)
    
@bot.command(name='ping')
async def ping(ctx):
    start_time = time.time()
    message = await ctx.send("Измеряю пинг...")
    end_time = time.time()
    ping_time = round((end_time - start_time) * 1000)
    await message.edit(content=f"Время пинга: {ping_time} мс")

# Функция для генерации нового курса криптовалюты
def generate_crypto_prices():
    for currency in CRYPTO_LIST:
        change_percent = random.uniform(-5, 5)  # Изменение на случайный процент от -5% до 5%
        CRYPTO_LIST[currency]['price'] *= (1 + change_percent / 100)  # Применяем изменение

# Замените функцию crypto_prices_generator() следующим кодом:
async def crypto_prices_generator():
    while True:
        await asyncio.sleep(600)  # Пауза в 10 минут
        generate_crypto_prices()
        save_crypto_prices()

# Замените код в функции crypto_prices_cmd() следующим кодом:
@bot.command(name='crypto_prices')
async def crypto_prices_cmd(ctx):
    prices_str = '\n'.join([f"{CRYPTO_LIST[currency]['emoji']} {currency.capitalize()}: {CRYPTO_LIST[currency]['price']} USD" for currency in CRYPTO_LIST])
    await ctx.send(f"Текущие курсы криптовалют:\n{prices_str}")

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

# Команда для добавления администратора
@bot.command(name='add_admin')
@commands.has_permissions(administrator=True)
async def add_admin(ctx, member: discord.Member):
    admin_data_path = os.path.join(ADMIN_DATA_DIR, str(ctx.guild.id), "admins.json")
    admin_dir = os.path.join(ADMIN_DATA_DIR, str(ctx.guild.id))

    if not os.path.exists(admin_dir):
        os.makedirs(admin_dir)

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
@bot.command(name='rem_admin')
@commands.has_permissions(administrator=True)
async def rem_admin(ctx, member: discord.Member):
    admin_data_path = os.path.join(ADMIN_DATA_DIR, str(ctx.guild.id), "admins.json")

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

# Функция для сохранения текущих курсов криптовалют
def save_crypto_prices():
    with open("crypto_prices.json", "w") as file:
        json.dump(CRYPTO_LIST, file)

# Функция для загрузки текущих курсов криптовалют из файла
def load_crypto_prices():
    if os.path.exists("crypto_prices.json"):
        with open("crypto_prices.json", "r") as file:
            return json.load(file)
    else:
        return CRYPTO_LIST

# Команда для обмена криптовалюты по текущему курсу
# Синтаксис команды: /exchange [валюта_от] [валюта_в] [количество]
# Пример использования: /exchange bitcoin bananacoin 10
@bot.command(name='exchange')
async def exchange_cmd(ctx, currency_from: str, currency_to: str, amount: int):
    await exchange_crypto(ctx, currency_from.lower(), currency_to.lower(), amount)

# Функция для обмена криптовалюты по текущему курсу
async def exchange_crypto(ctx, currency_from, currency_to, amount):
    if currency_from in CRYPTO_LIST and currency_to in CRYPTO_LIST:
        if currency_from != currency_to:
            user_data = load_user_data(ctx.guild.id, ctx.author.id)
            crypto_wallet = user_data.get("crypto_wallet", {})
            if crypto_wallet.get(currency_from, 0) >= amount:
                exchange_rate = CRYPTO_LIST[currency_to]['price'] / CRYPTO_LIST[currency_from]['price']
                received_amount = int(amount * exchange_rate)
                crypto_wallet[currency_from] -= amount
                crypto_wallet[currency_to] = crypto_wallet.get(currency_to, 0) + received_amount
                user_data["crypto_wallet"] = crypto_wallet
                save_user_data(ctx.guild.id, ctx.author.id, user_data)
                await ctx.send(f"{ctx.author.mention}, вы обменяли {amount} {CRYPTO_LIST[currency_from]['emoji']} {currency_from.capitalize()} на {received_amount} {CRYPTO_LIST[currency_to]['emoji']} {currency_to.capitalize()}.")
            else:
                await ctx.send("У вас недостаточно указанной криптовалюты.")
        else:
            await ctx.send("Нельзя обменять криптовалюту на ту же самую.")
    else:
        await ctx.send("Указанной криптовалюты нет в списке доступных.")

def main():
    server_id = "your_server_id_value"
    file_checker("work_message.txt", server_id)
    bot.last_work_time = {}
    bot.last_steal_time = {}
    bot.loop.create_task(crypto_prices_generator())  # Создание задачи генерации курсов криптовалют
    token = get_token()
    if token is not None:
        bot.run(token)
    else:
        logger.error("Не удалось получить токен. Бот выключается...")

if __name__ == '__main__':
    main()
