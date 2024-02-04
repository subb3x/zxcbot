import disnake
from disnake.ext import commands
from cogs.config import settings
from databases import db
import os


class PersistentViewBot(commands.Bot):
    def __init__(self):
        db.create_tables()
        self.cogs_list = [file[:-3] for file in os.listdir('./cogs') if file.endswith('.py')]
        self.mod_cogs_list = [file[:-3] for file in os.listdir('./cogs/moderation') if file.endswith('.py')]
        self.choices = self.cogs_list + self.mod_cogs_list
        super().__init__(command_prefix=settings['prefix'], intents=disnake.Intents.all(),
                         activity=disnake.Game(name='zxc lobby 1v1'), status=disnake.Status.do_not_disturb)
        self.persistent_views_added = False

    async def on_ready(self):
        if not self.persistent_views_added:
            self.persistent_views_added = True
        print('-------------------------------- \nЗхцбот запущен, лоббачок создан \n--------------------------------')


bot = PersistentViewBot()

for file in os.listdir('./cogs'):
    if file.endswith('.py'):
        bot.load_extension(f'cogs.{file[:-3]}')

for file in os.listdir('./cogs/moderation'):
    if file.endswith('.py'):
        bot.load_extension(f'cogs.moderation.{file[:-3]}')


@bot.slash_command(description='Загрузить модуль бота', guild_ids=settings['test_guilds'])  # Эта команда отвечает за загрузку когов
@commands.has_permissions(administrator=True)
@commands.is_owner()
async def load(inter: disnake.CommandInteraction,
               module: str = commands.Param(name="module", description="Название модуля", choices=bot.choices)):
    try:
        if module in bot.cogs_list:
            bot.load_extension(f"cogs.{module}")
        elif module in bot.mod_cogs_list:
            bot.load_extension(f"cogs.moderation.{module}")
        else:
            await inter.response.send_message(f"Модуль `{module}` не найден", ephemeral=True)
            return
        await inter.response.send_message(f"Загружен модуль `{module}`", ephemeral=True)
    except disnake.ext.commands.errors.NotOwner:
        await inter.response.send_message(f"Для выполнения этой команды нужно быть владельцем бота", ephemeral=True)


@bot.slash_command(description='Выгрузить модуль бота', guild_ids=settings['test_guilds'])  # Эта команда отвечает за выгрузку когов (отключение)
@commands.has_permissions(administrator=True)
@commands.is_owner()
async def unload(inter: disnake.CommandInteraction,
                 module: str = commands.Param(name="module", description="Название модуля", choices=bot.choices)):
    try:
        if module in bot.cogs_list:
            bot.unload_extension(f"cogs.{module}")
        elif module in bot.mod_cogs_list:
            bot.unload_extension(f"cogs.moderation.{module}")
        else:
            await inter.response.send_message(f"Модуль `{module}` не найден", ephemeral=True)
            return
        await inter.response.send_message(f"Выгружен модуль `{module}`", ephemeral=True)
    except disnake.ext.commands.errors.NotOwner:
        await inter.response.send_message(f"Для выполнения этой команды нужно быть владельцем бота", ephemeral=True)


@bot.slash_command(description="Перезагрузить модуль бота", guild_ids=settings['test_guilds']) # Эта команда отвечает за перезагрузку когов (т.е необязательно перезагружать бота, можно перезагрузить сам ког)
@commands.has_permissions(administrator=True)
@commands.is_owner()
async def reload(inter: disnake.CommandInteraction,
                 module: str = commands.Param(name="module", description="Название модуля", choices=bot.choices)):
    try:
        if module in bot.cogs_list:
            bot.reload_extension(f"cogs.{module}")
        elif module in bot.mod_cogs_list:
            bot.reload_extension(f"cogs.moderation.{module}")
        else:
            await inter.response.send_message(f"Модуль `{module}` не найден", ephemeral=True)
            return
        await inter.response.send_message(f"Перезагружен модуль `{module}`", ephemeral=True)
    except disnake.ext.commands.errors.NotOwner:
        await inter.response.send_message(f"Для выполнения этой команды нужно быть владельцем бота", ephemeral=True)

@bot.slash_command(description="Перезагрузить все модули", guild_ids=settings['test_guilds'])
@commands.is_owner()
async def reload_all(inter: disnake.CommandInteraction): # Эта команда отвечает за перезагрузку всех когов
    try:
        for file in os.listdir('./cogs'):
            if file.endswith('.py'):
                bot.reload_extension(f'cogs.{file[:-3]}')

        for file in os.listdir('./cogs/moderation'):
            if file.endswith('.py'):
                bot.reload_extension(f'cogs.moderation.{file[:-3]}')
        await inter.response.send_message(f"Все модули успешно перезагружены", ephemeral=True)
    except disnake.ext.commands.errors.NotOwner:
        await inter.response.send_message(f"Для выполнения этой команды нужно быть владельцем бота", ephemeral=True)


bot.run(settings['token'])
