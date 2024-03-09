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
FAILED_STEAL_MIN_LOSS = 1 # Минимальная потеря монет в /steal
FAILED_STEAL_MAX_LOSS = 350 # Максимальная потеря монет в /steal
# Начальные цены для криптовалют
CRYPTO_LIST = {
    'bitcoin': {'emoji': ':dvd:', 'price': 50000},
    'ethereum': {'emoji': ':cd:', 'price': 10000},
    'bananacoin': {'emoji': ':banana:', 'price': 250}
}

logger = logging.getLogger('discord_bot')
intents = discord.Intents.default()
intents.messages = True

logging.basicConfig(format='%(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

bot = commands.Bot(command_prefix='/', intents=intents)

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

# Проверка файлов перед запуском
def file_checker(server_id):
    ensure_server_data_dir(server_id)

def user_data_path(server_id, user_id):
    return os.path.join(SERVERS_DATA_DIR, str(server_id), f"{user_id}.json")

# Декоратор для проверки, является ли пользователь администратором
def isAdmin(ctx):
    admin_data_path = os.path.join(SERVERS_DATA_DIR, str(ctx.guild.id), "admins.json")
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
    user_balance = user_data.get("money", 0)
    user_balance += currency_earned
    user_data["money"] = user_balance
    save_user_data(server_id, user_id, user_data)
    work_message = work_message.replace("{currency_earned}", str(currency_earned))
    await ctx.send(f'{ctx.author.mention}, {work_message}.')

# Команда для просмотра текущего баланса и криптовалют
@bot.command(name='balance')
async def balance_cmd(ctx):
    user_id = str(ctx.author.id)
    server_id = str(ctx.guild.id)
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
    
    await ctx.send(f'{ctx.author.mention}, ваш текущий баланс:\n\n{balance_str}{crypto_str}')

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
    if random.random() < 0.4567:  # Шанс 45,67%
        stolen_amount = random.randint(20, 265)
        with open("steal_message.txt", "r", encoding="utf-8") as file:
            messages = file.readlines()
            steal_message = random.choice(messages).strip()
        user_data = load_user_data(server_id, user_id)
        user_balance = user_data.get("money", 0)
        user_balance += stolen_amount
        user_data["money"] = user_balance
        save_user_data(server_id, user_id, user_data)
        steal_message = steal_message.replace("{stolen_amount}", str(stolen_amount))
        await ctx.send(f'{ctx.author.mention}, {steal_message}')
    else:
        lost_amount = random.randint(FAILED_STEAL_MIN_LOSS, FAILED_STEAL_MAX_LOSS)
        user_data = load_user_data(server_id, user_id)
        user_balance = user_data.get("money", 0)
        user_balance = max(0, user_balance - lost_amount)  
        user_data["money"] = user_balance
        save_user_data(server_id, user_id, user_data)
        await ctx.send(f'{ctx.author.mention}, попытка украсть провалилась! Вы потеряли {lost_amount} монет.')
    
@bot.command(name='ping')
async def ping(ctx):
    start_time = time.time()
    message = await ctx.send("Пингую... :ping_pong:")
    end_time = time.time()
    ping_time = round((end_time - start_time) * 1000)
    await message.edit(content=f"Ваш пинг: {ping_time} мс")

# Команда для добавления администратора
@bot.command(name='add_admin')
@commands.has_permissions(administrator=True)
async def add_admin(ctx, member: discord.Member):
    admin_data_path = os.path.join(SERVERS_DATA_DIR, str(ctx.guild.id), "admins.json")
    admin_dir = os.path.join(SERVERS_DATA_DIR, str(ctx.guild.id))

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
    admin_data_path = os.path.join(SERVERS_DATA_DIR, str(ctx.guild.id), "admins.json")

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
@bot.command(name='crypto_prices')
async def crypto_prices_cmd(ctx):
    prices_str = '\n'.join([f"{CRYPTO_LIST[currency]['emoji']} {currency.capitalize()}: {CRYPTO_LIST[currency]['price']} :coin:" for currency in CRYPTO_LIST])
    await ctx.send(f"Текущие курсы криптовалют:\n{prices_str}")

# Функция для генерации новых цен криптовалют
def generate_crypto_prices():
    for currency in CRYPTO_LIST:
        change_percent = random.uniform(-1, 1)  # Изменение на случайный процент от -1% до 1%
        if random.random() < 0.05:  # Шанс 5% на редкое изменение
            change_percent *= random.uniform(0.8, 1.2)  # Редкое изменение от -20% до 20%
        CRYPTO_LIST[currency]['price'] *= (1 + change_percent / 100)  # Применяем изменение
    # Округляем цены криптовалют до нуля знаков после запятой/точки
    for currency in CRYPTO_LIST:
        CRYPTO_LIST[currency]['price'] = round(CRYPTO_LIST[currency]['price'])
    print("Изменились цены криптовалют!")

# Цикл меняющий цены раз в 10 минут
async def crypto_prices_generator():
    while True:
        await asyncio.sleep(600)  # Пауза в 10 минут
        generate_crypto_prices()
        save_crypto_prices()

# Функция для сохранения текущих курсов криптовалют
def save_crypto_prices():
    with open("crypto_prices.json", "w") as file:
        json.dump(CRYPTO_LIST, file)
        print("Сохранены курсы криптовалют!")

# Функция для загрузки текущих курсов криптовалют из файла
def load_crypto_prices():
    if os.path.exists("crypto_prices.json"):
        with open("crypto_prices.json", "r") as file:
            print("Загружены курсы криптовалют!")
            return json.load(file)
    else:
        print("Загружены начальные курсы криптовалют! Проверьте файл crypto_prices.json!")
        return CRYPTO_LIST

# Функция для загрузки текущих курсов криптовалют из файла
def load_crypto_prices():
    if os.path.exists("crypto_prices.json"):
        with open("crypto_prices.json", "r") as file:
            print("Загружены курсы криптовалют!")
            return json.load(file)
    else:
        print("Загружены курсы криптовалют!")
        return CRYPTO_LIST

@admin_command
@bot.command()
async def give_money(ctx, member: discord.Member, amount: int):
    # Проверка наличия всех аргументов
    if not member or amount is None:
        await ctx.send("Пожалуйста, используйте команду в формате: /give_money @пользователь количество")
        return

    # Загрузка данных пользователя
    user_id = str(ctx.author.id)
    server_id = str(ctx.guild.id)
    user_data = load_user_data(server_id, user_id)

    # Добавление денег пользователю
    user_data['money'] = user_data.get('money', 0) + amount

    # Отправка сообщения о выдаче денег
    await ctx.send(f'Пользователь {member.mention} (ID: {member.id}) получил {amount} денег.')

    # Сохранение данных пользователя после выдачи денег
    save_user_data(server_id, user_id, user_data)

@admin_command
@bot.command()
async def take_money(ctx, member: discord.Member, amount: int):
    # Проверка наличия всех аргументов
    if not member or amount is None:
        await ctx.send("Пожалуйста, используйте команду в формате: /take_money @пользователь количество")
        return

    # Загрузка данных пользователя
    user_id = str(member.id)
    server_id = str(ctx.guild.id)
    user_data = load_user_data(server_id, user_id)

    # Проверка достаточности денег у пользователя
    if user_data.get('money', 0) < amount:
        await ctx.send(f'У пользователя {member.mention} (ID: {member.id}) недостаточно денег.')
        return           

    # Отнимание денег у пользователя
    user_data['money'] -= amount

    # Отправка сообщения об отнятии денег
    await ctx.send(f'У пользователя {member.mention} (ID: {member.id}) отняли {amount} денег.')

    # Сохранение данных пользователя после отнятия денег
    save_user_data(server_id, user_id, user_data)

@admin_command
@bot.command()
async def give_crypto(ctx, currency: str, member: discord.Member, amount: int):
    # Проверка наличия всех аргументов
    if not currency or not member or amount is None:
        await ctx.send("Пожалуйста, используйте команду в формате: /give_crypto криптовалюта @пользователь количество")
        return

    # Проверка наличия указанной криптовалюты в списке
    if currency.lower() not in CRYPTO_LIST:
        await ctx.send(f'Криптовалюта {currency} не найдена в списке доступных криптовалют.')
        return

    # Загрузка данных пользователя
    user_id = str(ctx.author.id)
    server_id = str(ctx.guild.id)
    user_data = load_user_data(server_id, user_id)

    # Добавление указанной криптовалюты пользователю
    user_data[currency.lower()] = user_data.get(currency.lower(), 0) + amount

    # Отправка сообщения о выдаче криптовалюты
    await ctx.send(f'Пользователь {member.mention} (ID: {member.id}) получил {amount} {currency}.')

    # Сохранение данных пользователя после выдачи криптовалюты
    save_user_data(server_id, user_id, user_data)

@admin_command
@bot.command()
async def take_crypto(ctx, currency: str, member: discord.Member, amount: int):
    # Проверка наличия всех аргументов
    if not currency or not member or amount is None:
        await ctx.send("Пожалуйста, используйте команду в формате: /take_crypto криптовалюта @пользователь количество")
        return

    # Проверка наличия указанной криптовалюты в списке
    if currency.lower() not in CRYPTO_LIST:
        await ctx.send(f'Криптовалюта {currency} не найдена в списке доступных криптовалют.')
        return

    # Загрузка данных пользователя
    user_id = str(member.id)
    server_id = str(ctx.guild.id)
    user_data = load_user_data(server_id, user_id)

    # Проверка достаточности указанной криптовалюты у пользователя
    if user_data.get(currency.lower(), 0) < amount:
        await ctx.send(f'У пользователя {member.mention} (ID: {member.id}) недостаточно {currency}.')
        return

    # Отнимание указанной криптовалюты у пользователя
    user_data[currency.lower()] -= amount

    # Отправка сообщения об отнятии криптовалюты
    await ctx.send(f'У пользователя {member.mention} (ID: {member.id}) отняли {amount} {currency}.')

    # Сохранение данных пользователя после отнятия криптовалюты
    save_user_data(server_id, user_id, user_data)

# Удаляем предустановленную команду help
bot.remove_command("help")
@bot.command()
async def help(ctx):
    message = (
        ":bulb: Префикс ВСЕХ команд бота: /\n"
        ":rosette: /start - Высвечивает стартовое сообщение\n"
        ":rosette: /SideJob - Команда для быстрого, но маленького заработка\n"
        ":rosette: /steal - Команда для еще более быстрого но более рискового заработка\n"
        ":rosette: /balance - Позволяет просмотреть ваш баланс\n"
        ":rosette: /crypto_prices - Просмотреть текущую стоимость криптовалют (Да, да, она меняется)\n"
        ":rosette: /ping - Проверить время ответа бота, в основном для администраторов, но и обычным людям тоже доступна\n"
        ":rosette: /admin_help - Тот же самый /help, но для администраторов\n"
        ":rosette: /promo - Команда для взаимодействия с промокодами\n"
    )
    await ctx.send(message)

@bot.command()
async def admin_help(ctx):
    message = (
        ":bulb: Префикс для ВСЕХ команд бота: /\n"
        ":bulb: Эти команды ТОЛЬКО для администрации, обычным людям они не нужны\n"
        ":rosette: /give_money - Выдаёт монеты, без аргументов ничего не делает, синтаксис: /give_money @(пинг) (кол-во монет)\n"
        ":rosette: /take_money - Забирает монет, без аргументов ничего не делает, синтаксис: /take_money @(пинг) (кол-во монет)\n"
        ":rosette: /give_crypto - Выдаёт криптовалюты, без аргументов ничего не делает, синтаксис: /give_crypto (валюта) @(пинг) (кол-во)\n"
        ":rosette: /take_crypto - Забирает криптовалюты, без аргументов ничего не делает, синтаксис: /take_crypto (валюта) @(пинг) (кол-во)\n"
        ":rosette: /add_admin - Добавляет нового администратора\n"
        ":rosette: /rem_admin - Удаляет администратора\n"
        ":rosette: /change_crypto_prices - Мгновенно меняет цены криптовалюты\n"
    )
    await ctx.send(message)

@admin_command
@bot.command(name='change_crypto_prices')
async def change_crypto_prices(ctx):
    print("Кто-то принудительно изменил цены криптовалют!")
    generate_crypto_prices()
    await ctx.send("Вы принудительно изменили цены криптовалют!")

@bot.command
async def promo(ctx):
    await ctx.send("В разработке")

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
    server_id = "no_server_id_now"
    file_checker(server_id)
    load_crypto_prices()
    bot.last_work_time = {}
    bot.last_steal_time = {}
    bot.loop.create_task(crypto_prices_generator())
    bot.run(get_token())

if __name__ == "__main__":
    main()
