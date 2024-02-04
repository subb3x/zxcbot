import disnake
from disnake.ext import commands
from databases import db


class VoiceCreation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = db.Session()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: disnake.Member, before, after): # Функция, отвечающая за создание голосовых каналов
        guild = member.guild
        channel_id = self.session.query(db.Configs).filter_by(guild=guild.id).first().voice_channel_id
        category_id = self.session.query(db.Configs).filter_by(guild=guild.id).first().voice_category_id
        category = guild.get_channel(category_id)
        muted = guild.get_role(
            self.session.query(db.Configs).filter(db.Configs.guild == guild.id).first().muted_role_id)

        overwrites = {
            member: disnake.PermissionOverwrite(manage_channels=True),
            muted: disnake.PermissionOverwrite(speak=False, stream=False, send_messages=False)
        }

        if after.channel and after.channel.id == channel_id:
            vc = await guild.create_voice_channel(f"Канал {member.display_name}", overwrites=overwrites,
                                                  category=category)
            await member.move_to(vc)

        if category and category.type == disnake.ChannelType.category:
            for channel in category.voice_channels:
                if not channel.members:
                    await channel.delete()


def setup(bot):
    bot.add_cog(VoiceCreation(bot))
