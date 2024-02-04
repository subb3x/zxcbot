import disnake
from disnake.ext import commands
from cogs.config import fields_additional, fields_main


class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description='Для вывода информации о боте') # Выводит информацию о боте в виде эмбеда
    async def info(self, inter: disnake.ApplicationCommandInteraction):
        embed_main = disnake.Embed(title="Для чего можно использовать этого бота?", colour=16333380)
        embed_additional = disnake.Embed(title="Немного информации о создателе:", colour=16333380)

        for name, value in fields_main.items():
            embed_main.add_field(name=name, value=value, inline=False)

        for name, value in fields_additional.items():
            embed_additional.add_field(name=name, value=value, inline=False)

        await inter.response.send_message(embed=embed_main, ephemeral=True)
        await inter.followup.send(embed=embed_additional, ephemeral=True)


def setup(bot):
    bot.add_cog(Info(bot))
