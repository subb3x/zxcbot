import disnake
from disnake.ext import commands
from databases import db
import os

class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = db.Session()
    @commands.Cog.listener()
    async def on_message_delete(self, message: disnake.Message): # Отправляет удаленные сообщения в специальный канал (если есть)
        guild = message.guild
        log_channel = guild.get_channel(self.session.query(db.Configs).filter_by(guild=guild.id).first().log_channel_id)
        if log_channel is not None:
            report_channel = guild.get_channel(self.session.query(db.Configs).filter_by(guild=guild.id).first().reports_channel_id)
            if message.channel is not log_channel and message.channel is not report_channel:
                embed = disnake.Embed(
                    title=f"Удаленное сообщение из канала: {message.channel}",
                    colour=16333380)
                embed.set_author(
                    name=message.author,
                    icon_url=message.author.display_avatar.url)
                embed.add_field(
                    name="Сообщение:",
                    value=f"- {message.content}",
                    inline=False)
                if message.attachments:
                    for attachment in message.attachments:
                        await attachment.save(f"logged_files/{attachment.filename}")
                        with open(f"logged_files/{attachment.filename}", "rb") as file:
                            await log_channel.send(
                                content="Прикрепленные файлы:",
                                embed=embed,
                                file=disnake.File(file, attachment.filename))
                            file.close()
                            os.remove(f"logged_files/{attachment.filename}")
                else:
                    await log_channel.send(embed=embed)



def setup(bot):
    bot.add_cog(Logs(bot))