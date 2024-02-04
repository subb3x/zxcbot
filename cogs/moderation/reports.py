import disnake
from disnake.ext import commands
from databases import db


class Reports(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = db.Session()

    @commands.slash_command(description="Пожаловаться на пользователя") # Команда для репорта пользователя
    async def report(self,inter: disnake.ApplicationCommandInteraction,
                     person: disnake.Member = commands.Param(name="person", description="Пользователь"),
                     reason: str = commands.Param(name="reason", description="Причина")):
        report_found = False
        guild = inter.guild
        reports = guild.get_channel(self.session.query(db.Configs).filter_by(guild=guild.id).first().reports_channel_id)
        if reports is not None:
            async for report_message in reports.history(limit=None):
                if f"Репорт на пользователя: {person}\nОт пользователя: {inter.author}" in report_message.content:
                    report_found = True
                    break
            if report_found:
                await inter.response.send_message("Репорт на данного пользователя уже был вами отправлен", ephemeral=True)
            else:
                if person == inter.author:
                    await inter.response.send_message("Вы не можете зарепортить себя", ephemeral=True)
                    await inter.response.send_message("Вы не можете зарепортить себя", ephemeral=True)
                else:
                    report_text = f"**Репорт на пользователя:** {person.mention} \n" \
                                  f"**От пользователя:** {inter.author.mention} \n" \
                                  f"**По причине:** {reason} \n" \
                                  f"**На рассмотрение** {inter.guild.owner.mention}"
                    await reports.send(report_text, components=[disnake.ui.Button(label='Закрыть репорт',
                                                                                  style=disnake.ButtonStyle.success,
                                                                                  custom_id="close_report"),
                                                                disnake.ui.Button(label='Выдать предупреждение',
                                                                                  style=disnake.ButtonStyle.danger,
                                                                                  custom_id="warn_report"),
                                                                disnake.ui.Button(label='Замутить пользователя',
                                                                                  style=disnake.ButtonStyle.danger,
                                                                                  custom_id="mute_report"),
                                                                disnake.ui.Button(label='Забанить пользователя',
                                                                                  style=disnake.ButtonStyle.danger,
                                                                                  custom_id="ban_report")])
                    await inter.response.send_message("Репорт на пользователя успешно отправлен.", ephemeral=True)
        else:
            await inter.response.send_message("К сожалению, на данном сервере не настроены репорты :с", ephemeral=True)

    @commands.Cog.listener()
    async def on_button_click(self, inter: disnake.MessageInteraction):
        if inter.component.custom_id == "close_report": # Кнопка, удаляющая сообщение с репортом (по сути закрывающая его)
            await inter.message.delete()
        if inter.component.custom_id == "ban_report": # Кнопка, банящая зарепорченного пользователя
            guild = inter.guild
            reports = guild.get_channel(
                self.session.query(db.Configs).filter_by(guild=guild.id).first().reports_channel_id)
            message_lines = inter.message.content.split("\n")
            reported_user_id = int(message_lines[0].split()[-1][2:-1])
            reported_user = disnake.utils.get(guild.members, id=reported_user_id)
            reason = ' '.join(str(element) for element in message_lines[2].split()[2:])
            await reported_user.send(f"Вы были забанены на сервере {guild.name} по причине:\n{reason}")
            await inter.guild.ban(reported_user, reason=reason)
            await reports.send(f'Пользователь {reported_user.mention} был забанен по причине:\n{reason}')
            await inter.message.delete()

                # Eng: The warn's and mute's buttons are located in the warns.py and mutes.py
                # Rus: Кнопки предупреждения и мута находятся в warns.py и mutes.py


def setup(bot):
    bot.add_cog(Reports(bot))
