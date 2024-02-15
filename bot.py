import os
import discord
from discord.ext import commands
import logging
import threading
import time

def loading_animation():
    symbols = ['-', '/', '|', '\\']
    index = 0
    while not done:
        print(f'Запуск бота... {symbols[index]} - Последнее действие: {last_action}', end='\r')
        index = (index + 1) % len(symbols)
        time.sleep(0.25)

done = False
last_action = None

def bot_action(action):
    global last_action
    last_action = action

# Запускаем анимацию в отдельном потоке
thread = threading.Thread(target=loading_animation)
thread.start()

bot_action('Инициализация')

logger = logging.getLogger('discord_bot')
intents = discord.Intents.default()
intents.messages = True

bot = commands.Bot(command_prefix='/', intents=intents)

# Штучка консольку чистить
def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

@bot.command(name='start')
async def start_cmd(ctx):
    user_name = ctx.author.name
    guild_name = ctx.guild.name
    await ctx.send(f'Приветствую, это на данный момент тестовая команда. Все команды: /help Имя бота: {bot.user.name}. Твой юзернейм: {user_name}. Имя сервера: {guild_name}. Тестовое эмодзи: :fly: ')

def Main():
    bot_action('Бот запущен')
    global done
    # Выводим логи в консоль
    logging.basicConfig(format='%(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)
    # Останавливаем анимацию
    done = True
    thread.join()
    clear_console()

    # Запускаем бота

    bot.add_command('work')
    bot.run('MTIwMzc0ODgyMDAwMjAxNzM3MQ.G6ESsa.TGwsXWtdhFGK_JOyOU2FMrMYEbSf1ltcQLQDsw')
