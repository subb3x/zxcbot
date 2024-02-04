import disnake
from disnake.ext import commands
from databases import db

class Autorole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = db.Session()

    @commands.Cog.listener() # Выдает роль каждому новичку, который заходит на сервер
    async def on_member_join(self, member: disnake.Member):
        role = member.guild.get_role(self.session.query(db.Configs).filter_by(guild=member.guild.id).first().autorole_id)
        if role is not None:
            await member.add_roles(role)

def setup(bot):
    bot.add_cog(Autorole(bot))