import disnake
from disnake.ext import commands, tasks
from databases import db
import datetime


class Warns(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = db.Session()
        bot.loop.create_task(self.on_ready())

    async def on_ready(self):
        await self.bot.wait_until_ready()
        self.check_warns.start()


    @commands.slash_command(description='Выдать предупреждение') # Команда для выдачи варна пользователю
    @commands.has_permissions(ban_members=True)
    async def warn(self, inter,
                   user: disnake.Member = commands.Param(name='user', description='Пользователь для выдачи предупреждения'),
                   reason: str = commands.Param(name='reason', description='Причина выдачи предупреждения')):
        guild = inter.guild
        ban_reason = "Превышено количество предупреждений"
        warns_duration = self.session.query(db.Configs).filter_by(guild=guild.id).first().warns_duration
        warns_max = self.session.query(db.Configs).filter_by(guild=guild.id).first().warns_max
        self.session.add(db.Warns(username=user.name,
                                  end_date=datetime.datetime.now() + datetime.timedelta(days=warns_duration),
                                  reason=reason,
                                  given_by=inter.author.id,
                                  given_date=datetime.datetime.now(),
                                  index=self.session.query(db.Warns).filter_by(guild=guild.id,
                                                                               username=user.name).count() + 1,
                                  guild=guild.id))
        await inter.response.send_message(f"Пользователю {user.mention} было выдано предупреждение \nПричина: {reason}", ephemeral=True)
        if self.session.query(db.Warns).filter_by(username=user.name, guild=guild.id, index=warns_max).first():
            self.session.query(db.Warns).filter_by(username=user.name, guild=guild.id).delete()
            await user.send(f"Вы были забанены на сервере {guild.name} по причине:\n{ban_reason}")
            await inter.guild.ban(user, reason=reason)
            await inter.channel.send(f'Пользователь {user.mention} был забанен по причине:\n{ban_reason}', ephemeral=True)
        self.session.commit()
        self.session.close()

    @commands.slash_command(description="Снять предупреждение") # Команда для снятия самого старого варна конкретного пользователя
    @commands.has_permissions(ban_members=True)
    async def unwarn(self, inter: disnake.ApplicationCommandInteraction, user: disnake.Member = commands.Param(
        name='user', description='Пользователь для снятия предупреждения'
    )): # Команда для снятия варна
        guild = inter.guild
        self.session.delete(self.session.query(db.Warns).filter_by(username=user.name, guild=guild.id).first())
        self.session.commit()
        self.session.close()
        await inter.response.send_message(f"Предупреждение с пользователя {user.mention} было снято", ephemeral=True)

    @commands.slash_command(description="Список предупреждений") # Команда, показывающая варны пользователя, который ее вызывает
    async def warns(self, inter: disnake.ApplicationCommandInteraction):
        guild = inter.guild
        warns_max = self.session.query(db.Configs).filter_by(guild=guild.id).first().warns_max
        embed = disnake.Embed(title=f"Предупреждения",
                              description=f"При получении {warns_max} предупреждений вы будете автоматически забанены на сервере",
                              colour=16333380)
        embed.set_author(name=inter.author, icon_url=inter.author.display_avatar.url)
        for warn in self.session.query(db.Warns).filter_by(username=inter.author.name, guild=guild.id).all():
            tdif = warn.end_date - datetime.datetime.now()
            embed.add_field(name=f"Предупреждение №{warn.index}:",
                            value=f"- Выдан: <@{warn.given_by}> \n"
                                  f"- Причина: {warn.reason} \n"
                                  f"- Будет снято через: {tdif.days}д, {tdif.seconds // 3600}ч, {tdif.seconds // 60 % 60}м и {tdif.seconds % 60}с", inline=False)
        if not embed.fields:
            embed.add_field(name="У вас пока нет предупреждений",
                            value="- И это превосходно, продолжайте в том же духе!",
                            inline=False)
        await inter.response.send_message(embed=embed, ephemeral=True)
        self.session.close()

    @commands.slash_command(description="Список предупреждений") # Команда, показывающая варны конкретного пользователя (только для модераторов)
    @commands.has_permissions(administrator=True)
    async def user_warns(self, inter: disnake.ApplicationCommandInteraction, user: disnake.Member = commands.Param(
        name='user', description='Пользователь для просмотра предупреждений'
    )):
        guild = inter.guild
        embed = disnake.Embed(title=f"Предупреждения", colour=16333380)
        embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
        for warn in self.session.query(db.Warns).filter_by(username=user.name, guild=guild.id).all():
            tdif = warn.end_date - datetime.datetime.now()
            embed.add_field(name=f"Предупреждение №{warn.index}:",
                            value=f"- Выдан: <@{warn.given_by}> \n"
                                  f"- Причина: {warn.reason} \n"
                                  f"- Будет снято через: {tdif.days}д, {tdif.seconds // 3600}ч, {tdif.seconds // 60 % 60}м и {tdif.seconds % 60}с", inline=False)
        if not embed.fields:
            embed.add_field(name="У этого пользователя пока нет предупреждений",
                            value="- И это превосходно, видимо, он просто хорошо себя ведет!",
                            inline=False)
        await inter.response.send_message(embed=embed, ephemeral=True)
        self.session.close()

    @commands.slash_command(description='Список предупреждений') # Команда показывающая варны всех людей на сервере
    @commands.has_permissions(administrator=True)
    async def all_warns(self, inter: disnake.ApplicationCommandInteraction):
        guild = inter.guild
        warns = self.session.query(db.Warns).filter_by(guild=guild.id).all()
        warns_max = self.session.query(db.Configs).filter_by(guild=guild.id).first().warns_max
        default_embed = disnake.Embed(title=f"Предупреждения",
                                      description=f"Текущее максимальное кол-во предупреждений: {warns_max}\n"
                                                  f"Изменить это значение можно при помощи команды **/config (max_warns)**",
                                      colour=16333380).set_author(name=inter.author, icon_url=inter.author.display_avatar.url)
        embed = default_embed
        embeds = []
        for i, warn in enumerate(warns):
            if i == 25 or i == 50: # Если полей в варнах больше 25/50, то создаем новый эмбед
                embeds.append(embed)
                embed = default_embed

            if i == 75: # Если количество варнов переваливает за 75, то лучше вывести просто файлом (для крупных серверов)
                embeds.clear()
                embed = default_embed.add_field(name='Достигнут лимит',
                                                value='Превышено количество предупреждений для нормального отображения в эмбедах, поэтому к данному сообщению будет прикреплен файл с предупреждениями всех пользователей сервера',
                                                inline=False)
                with open(f'warns-{guild.id}') as f:
                    for warn in warns:
                        f.write(f'Пользователь: {warn.username} \n'
                                f'Выдан: <@{warn.given_by}> \n'
                                f'Причина: {warn.reason} \n'
                                f'Всего варнов у пользователя: {self.session.query(db.Warns).filter_by(username=warn.username, guild=guild.id).count()} \n'
                                f'Номер варна: {warn.index} \n'
                                f'Дата выдачи: {warn.given_date.strftime("%d.%m.%Y, %H:%M:%S")} \n'
                                f'Будет снято через: {tdif.days}д, {tdif.seconds // 3600}ч, {tdif.seconds // 60 % 60}м и {tdif.seconds % 60}с \n'
                                f'--------------------------------------\n')
                break
            # Добавляем каждый варн в эмбед
            tdif = warn.end_date - datetime.datetime.now()
            embed.add_field(name=f"Пользователь: {disnake.utils.get(guild.members, name=warn.username)} \n",
                            value=f"Выдан: <@{warn.given_by}> \n"
                                  f"Причина: {warn.reason} \n"
                                  f"Всего варнов у пользователя: {self.session.query(db.Warns).filter_by(username=warn.username, guild=guild.id).count()} \n"
                                  f"Номер варна: {warn.index} \n"
                                  f"Дата выдачи: {warn.given_date.strftime('%d.%m.%Y, %H:%M:%S')} \n"
                                  f"Будет снято через: {tdif.days}д, {tdif.seconds // 3600}ч, {tdif.seconds // 60 % 60}м и {tdif.seconds % 60}с", inline=False)

        # Если в эмбеде нет варнов, то добавляем в него сообщение об этом
        if not embed.fields:
            embed.add_field(name="На вашем сервере пока нет предупреждений",
                            value="- И это превосходно, продолжайте в том же духе!",
                            inline=False)

        embeds.append(embed)

        # Проверяем есть ли файл с варнами
        if f: # Если есть, то отправляем его вместе с эмбедом о превышении лимита
            await inter.response.send_message(embed=embeds[0], file=f, ephemeral=True)
        else: # Иначе отправляем просто эмбед с варнами
            await inter.response.send_message(embed=embeds[0], ephemeral=True)
            # И если эмбедов несколько, то отправляем и их
            for embed in embeds[1:]:
                await inter.followup.send(embed=embed, ephemeral=True)

        self.session.close()

    @tasks.loop(minutes=1) # Каждую минуту проверяет, истекли ли варны, и удаляет их если истекли
    async def check_warns(self):
        for warn in self.session.query(db.Warns).all():
            if warn.end_date < datetime.datetime.now():
                self.session.delete(warn)
        self.session.commit()
        self.session.close()

    @commands.Cog.listener()
    async def on_button_click(self, inter: disnake.MessageInteraction):
        if inter.component.custom_id == "warn_report":  # Кнопка, дающая варн зарепорченному пользователю
            guild = inter.guild
            message_lines = inter.message.content.split("\n")
            reported_user_id = int(message_lines[0].split()[-1][2:-1])
            reported_user = disnake.utils.get(guild.members, id=reported_user_id)
            await Warns.warn(inter, user=reported_user,
                             reason=' '.join(str(element) for element in message_lines[2].split()[2:]))

def setup(bot):
    bot.add_cog(Warns(bot))
