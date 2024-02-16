import os
import discord
from discord.ext import commands
import logging

logger = logging.getLogger('discord_bot')
intents = discord.Intents.default()
intents.messages = True

bot = commands.Bot(command_prefix='/', intents=intents)

def get_token():
    token_directory = os.path.dirname(os.path.abspath(__file__))
    token_file_path = os.path.join(token_directory, "TOKEN.txt")

    if os.path.exists(token_file_path):
        with open(token_file_path, "r") as file:
            token = file.read().strip()
            if token:
                return token
            else:
                print("Токен не найден в файле TOKEN.txt")
                return None
    else:
        print("Файл TOKEN.txt не найден")
        token = input("Введите токен: ")
        try:
            with open(token_file_path, "w") as file:
                file.write(token)
                print("Токен успешно записан в файл!")
            return token
        except Exception as e:
            print(f"Не удалось записать токен в файл: {e}")
            return None

token = get_token()

if token is not None:
    # Здесь вы можете использовать переменную token для запуска вашего бота
    pass
else:
    print("Не удалось получить токен. Программа будет закрыта.")
    exit()

@bot.event
async def on_ready():
    print(f"Бот запущен, его имя {bot.user.name}")

@bot.command(name='start')
async def start_cmd(ctx):
    user_name = ctx.author.name
    guild_name = ctx.guild.name
    await ctx.send(f'Приветствую, это на данный момент тестовая команда. Все команды: /help Имя бота: {bot.user.name}. Твой юзернейм: {user_name}. Имя сервера: {guild_name}. Тестовое эмодзи: :fly: ')

def Main():
    # Выводим логи в консоль
    logging.basicConfig(format='%(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)

    # Запускаем бота
    bot.run(token)

if __name__ == '__main__':
    Main()
