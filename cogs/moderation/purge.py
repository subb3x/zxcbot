import disnake
from disnake.ext import commands


class Purge(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description='Удалить определенное кол-во сообщений из канала') # Команда, очищающая n-ное кол-во сообщений в текущем канале
    @commands.has_permissions(manage_messages=True)
    async def purge(self, inter: disnake.ApplicationCommandInteraction, amount: int = commands.Param(
        name="amount",
        description="Кол-во сообщений для удаления",
    )):
        await inter.channel.purge(limit=amount)
        await inter.response.send_message(f'{amount} сообщений было удалено', ephemeral=True)


def setup(bot):
    bot.add_cog(Purge(bot))
