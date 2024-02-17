import os
import json
import discord
from discord.ext import commands
import logging
import random
import time

SERVERS_DATA_DIR = "servers_data"  # Папка с данными серверов

logger = logging.getLogger('discord_bot')
intents = discord.Intents.default()
intents.messages = True

logging.basicConfig(format='%(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

bot = commands.Bot(command_prefix='/', intents=intents)

# Проверка наличия файла и создание его при необходимости
def file_checker(file_path, server_id):
    if not os.path.exists(file_path):
        with open(file_path, 'w'):
            pass
        print(f"Файл {file_path} был создан.")
    else:
        print(f"Файл {file_path} уже существует.")
    server_dir = os.path.join(SERVERS_DATA_DIR, str(server_id))
    if not os.path.exists(server_dir):
        os.makedirs(server_dir)
    else:
        print(f"Папка {server_dir} уже существует.")

def user_data_path(server_id, user_id):
    return os.path.join(SERVERS_DATA_DIR, str(server_id), f"{user_id}.json")

def load_user_data(server_id, user_id):
    data_path = user_data_path(server_id, user_id)
    if os.path.exists(data_path):
        with open(data_path, "r") as f:
            return json.load(f)
    else:
        with open(data_path, "w") as f:
            json.dump({}, f)
        return {}

def save_user_data(server_id, user_id, data):
    data_path = user_data_path(server_id, user_id)
    with open(data_path, "w") as f:
        json.dump(data, f)

@bot.event
async def on_ready():
    print(f"Бот запущен, его имя {bot.user.name}")

def work_currency():
    return random.randint(15, 135)

@bot.command(name='start')
async def start_cmd(ctx):
    user_name = ctx.author.name
    guild_name = ctx.guild.name
    await ctx.send(f'Приветствую, это на данный момент тестовая команда. Все команды: /help Имя бота: {bot.user.name}. Твой юзернейм: {user_name}. Имя сервера: {guild_name}. Тестовое эмодзи: :fly: ')

@bot.command(name='work')
async def work_cmd(ctx):
    user_id = str(ctx.author.id)
    server_id = str(ctx.guild.id)
    current_time = time.time()
    last_work_time = bot.last_work_time.get(server_id, {})
    if user_id in last_work_time:
        time_elapsed = current_time - last_work_time[user_id]
        if time_elapsed < 60 * 15:
            time_left = 60 * 15 - time_elapsed
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
    await ctx.send(f'{ctx.author.mention}, ваш текущий баланс: {user_balance} валюты')

@bot.event
async def on_error(event, *args, **kwargs):
    logger.error(f"Произошла ошибка в событии {event}", exc_info=True)

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
    
@bot.command(name='ping')
async def ping(ctx):
    start_time = time.time()
    end_time = time.time()
    ping_time = round((end_time - start_time) * 1000)
    await ctx.send(f"Время пинга: {ping_time} мс")

def main():
    server_id = "your_server_id_value"
    file_checker("work_message.txt", server_id)
    bot.last_work_time = {}
    token = get_token()
    if token is not None:
        bot.run(token)
    else:
        logger.error("Не удалось получить токен. Бот выключается...")

if __name__ == '__main__':
    main()