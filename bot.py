import os
import json
import discord
from discord.ext import commands
import logging
import random
import time

# Переменные
SERVERS_DATA_DIR = "servers_data"  # Папка с данными серверов
WORK_COOLDOWN = 1 # Время в секундах между попытками зароботка
STEAL_COOLDOWN = 5  # Время в секундах между попытками кражи
FAILED_STEAL_MIN_LOSS = 1 # Минимальная потеря монет
FAILED_STEAL_MAX_LOSS = 350 # Максимальная потеря монет
BASE_JOIN_SAMPLE_FILE = "base-join-sample.txt" # Тут хранится базовый пример

logger = logging.getLogger('discord_bot')
intents = discord.Intents.default()
intents.messages = True

logging.basicConfig(format='%(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    print(f"Bot is ready, logged in as {bot.user.name}")

# Проверка наличия папки сервера и создание ее, если она отсутствует
def ensure_server_data_dir(server_id):
    server_dir = os.path.join(SERVERS_DATA_DIR, str(server_id))
    if not os.path.exists(server_dir):
        os.makedirs(server_dir)

# В начале файла, после импортов и объявления переменных
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

def work_currency():
    return random.randint(15, 135)

@bot.event
async def on_member_join(member):
    server_id = str(member.guild.id)
    data_dir = os.path.join(SERVERS_DATA_DIR, server_id)
    join_sample_file = os.path.join(data_dir, "join_sample.txt")
    base_join_sample_file = os.path.join(BASE_JOIN_SAMPLE_FILE)

    if os.path.exists(join_sample_file):
        with open(join_sample_file, "r") as f:
            join_message = f.read()
    elif os.path.exists(base_join_sample_file):
        with open(base_join_sample_file, "r") as f:
            join_message = f.read()
    else:
        join_message = f"Welcome {member.mention} to {member.guild.name}!"

    join_message = join_message.replace("{user_name}", str(member))

    join_channel_file = os.path.join(data_dir, "join_channel.txt")

    if os.path.exists(join_channel_file):
        with open(join_channel_file, "r") as f:
            channel_id = int(f.read())
        channel = bot.get_channel(channel_id)
        if channel:
            await channel.send(join_message)

@bot.event
async def on_member_remove(member):
    server_id = str(member.guild.id)
    data_dir = os.path.join(SERVERS_DATA_DIR, server_id)
    leave_channel_file = os.path.join(data_dir, "leave_channel.txt")

    if os.path.exists(leave_channel_file):
        with open(leave_channel_file, "r") as f:
            channel_id = int(f.read())
        channel = bot.get_channel(channel_id)
        if channel:
            await channel.send(f"Goodbye {member}!")

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

    currency_earned = work_currency()

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

@bot.command(name='balance')
async def balance_cmd(ctx):
    user_id = str(ctx.author.id)
    server_id = str(ctx.guild.id)
    user_data = load_user_data(server_id, user_id)
    user_balance = user_data.get("balance", 0)
    await ctx.send(f'{ctx.author.mention}, ваш текущий баланс: {user_balance} :coin:')

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

@bot.command(name='set-join-ch')
async def set_join_channel(ctx):
    channel = ctx.message.channel
    server_id = str(ctx.guild.id)
    data_dir = os.path.join(SERVERS_DATA_DIR, server_id)

    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    with open(os.path.join(data_dir, "join_channel.txt"), "w") as f:
        f.write(str(channel.id))
    await ctx.send(f"Join channel set to {channel.mention}")

@bot.command(name='del-join-ch')
async def delete_join_channel(ctx):
    server_id = str(ctx.guild.id)
    data_dir = os.path.join(SERVERS_DATA_DIR, server_id)
    join_channel_file = os.path.join(data_dir, "join_channel.txt")

    if os.path.exists(join_channel_file):
        os.remove(join_channel_file)
        await ctx.send("Join channel deleted.")
    else:
        await ctx.send("Join channel not set.")

@bot.command(name='set-join-sample')
async def set_join_sample(ctx, *, template=None):
    server_id = str(ctx.guild.id)
    data_dir = os.path.join(SERVERS_DATA_DIR, server_id)

    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    if template:
        with open(os.path.join(data_dir, "join_sample.txt"), "w") as f:
            f.write(template)
        await ctx.send("Custom join sample set.")
    else:
        await ctx.send("Please provide a template.")

@bot.command(name='del-join-sample')
async def delete_join_sample(ctx):
    server_id = str(ctx.guild.id)
    data_dir = os.path.join(SERVERS_DATA_DIR, server_id)
    join_sample_file = os.path.join(data_dir, "join_sample.txt")

    if os.path.exists(join_sample_file):
        os.remove(join_sample_file)
        await ctx.send("Custom join sample deleted. Using base sample.")
    else:
        await ctx.send("Custom join sample not set.")

@bot.command(name='view-join-sample')
async def view_join_sample(ctx):
    server_id = str(ctx.guild.id)
    data_dir = os.path.join(SERVERS_DATA_DIR, server_id)
    join_sample_file = os.path.join(data_dir, "join_sample.txt")

    if os.path.exists(join_sample_file):
        with open(join_sample_file, "r") as f:
            join_sample = f.read()
        await ctx.send(f"Custom join sample:\n```{join_sample}```")
    else:
        await ctx.send("Custom join sample not set.")

@bot.command(name='restore-join-sample')
async def restore_join_sample(ctx):
    server_id = str(ctx.guild.id)
    data_dir = os.path.join(SERVERS_DATA_DIR, server_id)
    base_join_sample_file = os.path.join(BASE_JOIN_SAMPLE_FILE)

    if os.path.exists(base_join_sample_file):
        with open(base_join_sample_file, "r") as f:
            base_join_sample = f.read()

        join_sample_file = os.path.join(data_dir, "join_sample.txt")
        with open(join_sample_file, "w") as f:
            f.write(base_join_sample)

        await ctx.send("Join sample restored to default.")
    else:
        await ctx.send("Base join sample not found.")

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
    server_id = "your_server_id_value"
    file_checker("work_message.txt", server_id)
    bot.last_work_time = {}
    bot.last_steal_time = {}
    token = get_token()
    if token is not None:
        bot.run(token)
    else:
        logger.error("Не удалось получить токен. Бот выключается...")

if __name__ == '__main__':
    main()