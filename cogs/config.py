import disnake
from disnake.ext import commands
from databases import db
from sqlalchemy.inspection import inspect


class Config(commands.Cog):
    def __init__(self, bot):
        self.session = db.Session()
        self.bot = bot
        self.columns = [column.name for column in inspect(db.Configs).c][2:]

    @commands.slash_command(description='Показывает текущие настройки')
    @commands.has_permissions(administrator=True)
    async def show_config(self, inter: disnake.ApplicationCommandInteraction):  # Эта команда показывает текущие настройки в конфиге
        settings_dict = [row.__dict__ for row in self.session.query(db.Configs).filter_by(guild=inter.guild.id).all()][0]
        message = f"Текущие значения конфига:"
        for key in sorted(settings_dict.keys()):
            if key not in ['id', 'guild', '_sa_instance_state']:
                message += f" \n**{key}**: `{settings_dict[key]}`"
        await inter.response.send_message(message, ephemeral=True)

    @commands.slash_command(description='Настройка конфига сервера')
    @commands.has_permissions(administrator=True)
    async def config(self, inter: disnake.ApplicationCommandInteraction, setting: str, value): # Эта команда отвечает за настройку конфига
        self.session.query(db.Configs).filter_by(guild=inter.guild.id).update({setting: value})
        self.session.commit()
        self.session.close()
        await inter.response.send_message(f'Значение **{setting}** было успешно изменено на `{value}`', ephemeral=True)

    @config.autocomplete('setting')
    async def config_autocomplete(self, inter: disnake.ApplicationCommandInteraction, current: str): # Эта функция делает прописывание конфига более удобным засчет автокомплита
        settings_list = []
        db_guild = self.session.query(db.Configs).filter_by(guild=inter.guild.id).first()
        if db_guild is None:
            self.session.add(db.Configs(guild=inter.guild.id))
            self.session.commit()
            self.session.close()
            db_guild = self.session.query(db.Configs).filter_by(guild=inter.guild.id).first()
        for item in self.columns:
            db_value = db_guild.__getattribute__(item)
            if db_value is None:
                settings_list.append(item)
        choices = []
        if settings_list:
            for choice in settings_list:
                if current.lower() in choice.lower():
                    choices.append(disnake.OptionChoice(name=choice, value=choice))
        else:
            for choice in self.columns:
                if current.lower() in choice.lower():
                    choices.append(disnake.OptionChoice(name=choice, value=choice))
        return choices


def setup(bot):
    bot.add_cog(Config(bot))


settings = {
    'token': '',
    'prefix': 'zxc.',
    'test_guilds': [],
}

fields_main = {
    "Создание кастомных каналов пользователями": "- При заходе пользователем в специальный канал, создается его личный голосовой канал",
    "Модерация": "- Использование специальных команд (/mute, /warn /purge и т.д.) для упрощения модерации на сервере",
    "Автоматическая система ролей": "- Возможность назначить роль, выдаваемую каждому пользователю, заходящему на сервер",
    "Система репортов": "- Возможность для каждого участника сервера, отправить жалобу на другого участника, которая будет рассмотрена модераторами",
    "Система тикетов": "- Возможность пользователя задать любой вопрос, касающийся сервера и получить ответ от модераторов"
}

fields_additional = {
    "Автор бота:": "- Данный бот был создан subb3x (tg: @suptrix)",
    "Цель создания бота:": "- Данный бот был создан для портфолио и опубликован в GitHub: github.com/subb3x",
    "Канал автора:": "- Первоначальное расположение бота и по совместительству канал автора - дискорд канал floppaнцы: https://discord.gg/55Kwbs7FYb"
}
