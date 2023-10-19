import disnake
import disnake.voice_client
import datetime
from databases import db
from disnake.ext import commands, tasks
from config import *
import os

bot = commands.Bot(command_prefix=settings['prefix'], intents=disnake.Intents.all())


# INFO --------------------------------------------------------------------------------------------------
@bot.slash_command(description='Для вывода информации о боте')
async def info(inter: disnake.ApplicationCommandInteraction):
    embed_main = disnake.Embed(title="Для чего можно использовать этого бота?", colour=16333380)
    embed_additional = disnake.Embed(title="Немного информации о создателе:", colour=16333380)

    for name, value in fields_main.items():
        embed_main.add_field(name=name, value=value, inline=False)

    for name, value in fields_additional.items():
        embed_additional.add_field(name=name, value=value, inline=False)

    await inter.response.send_message(embed=embed_main, ephemeral=True)
    await inter.followup.send(embed=embed_additional, ephemeral=True)


# Moderation --------------------------------------------------------------------------------------------
@bot.slash_command(description='Удалить определенное кол-во сообщений из канала')
@commands.has_role(roles['moderators_role'])
async def purge(inter: disnake.ApplicationCommandInteraction, amount: int):
    await inter.channel.purge(limit=amount)
    await inter.response.send_message(f'{amount} сообщений было удалено', ephemeral=True)


# Mutes ---------------------------------------------------
@bot.slash_command(description='Выдать мут')
@commands.has_role(roles['moderators_role'])
async def mute(inter, user: disnake.Member, duration: str):
    db.create_tables()
    guild = inter.guild
    muted_role = inter.guild.get_role(roles['muted_role_id'])
    minutes = 0
    hours = 0
    days = 0
    duration_split = duration.split()

    for elem in duration_split:
        if 'd' in elem or 'д' in elem:
            days = int(elem[:-1])
        elif 'h' in elem or 'ч' in elem and int(elem[:-1]) < 24:
            hours = int(elem[:-1])
        elif ('m' in elem or 'м' in elem) and ('min' not in elem and 'мин' not in elem) and int(elem[:-1]) < 60:
            minutes = int(elem[:-1])
        elif 'min' in elem or 'мин' in elem and int(elem[:-3]) < 60:
            minutes = int(elem[:-3])

    session = db.Session()
    session.add(db.Mutes(username=user.name,
                         end_date=datetime.datetime.now() + datetime.timedelta(minutes=minutes,
                                                                               hours=hours,
                                                                               days=days),
                         guild=guild.id))
    session.commit()
    session.close()
    await user.add_roles(muted_role)
    if user.voice:
        previous_channel = user.voice.channel
        await user.move_to(channel=guild.get_channel(mute_reconnect))
        await user.move_to(previous_channel)
    await inter.response.send_message(f"Пользователь {user.mention} был замучен на {duration}",
                                      ephemeral=True)


@bot.slash_command(description='Снять мут')
@commands.has_role(roles['moderators_role'])
async def unmute(inter: disnake.ApplicationCommandInteraction, user: disnake.Member):
    guild = inter.guild
    muted_role = inter.guild.get_role(roles['muted_role_id'])
    session = db.Session()
    session.query(db.Mutes).filter(db.Mutes.username == user.name).delete()
    session.commit()
    session.close()
    await user.remove_roles(muted_role)
    if user.voice:
        previous_channel = user.voice.channel
        await user.move_to(channel=guild.get_channel(mute_reconnect))
        await user.move_to(previous_channel)
    await inter.response.send_message(f"Пользователь {user.mention} был размучен", ephemeral=True)


class MuteForm(disnake.ui.Modal):
    def __init__(self):
        components = [
            disnake.ui.TextInput(
                label="Длительность мута (в формате xд yч zм)",
                placeholder="Введите длительность мута",
                custom_id="mute_duration"
            ),
        ]
        super().__init__(title="Длительность мута", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        guild = inter.guild
        message_lines = inter.message.content.split("\n")
        reported_user_id = int(message_lines[0].split()[-1][2:-1])
        reported_user = disnake.utils.get(guild.members, id=reported_user_id)
        mute_duration = inter.text_values.get("mute_duration")
        await inter.message.delete()
        await mute(inter, user=reported_user, duration=mute_duration)


@tasks.loop(seconds=10)
async def check_mutes():
    session = db.Session()

    for muted_user in session.query(db.Mutes).filter(db.Mutes.end_date < datetime.datetime.now()).all():
        guild = bot.get_guild(muted_user.guild)
        user = disnake.utils.get(guild.members, name=muted_user.username)
        muted_role = guild.get_role(roles['muted_role_id'])
        session.delete(muted_user)
        await user.remove_roles(muted_role)
        if user.voice:
            previous_channel = user.voice.channel
            await user.move_to(channel=guild.get_channel(mute_reconnect))
            await user.move_to(previous_channel)

    session.commit()
    session.close()


# Warns --------------------------------------------------------------------------------
@bot.slash_command(description='Выдать предупреждение')
@commands.has_role(roles['moderators_role'])
async def warn(inter: disnake.ApplicationCommandInteraction, user: disnake.Member):
    session = db.Session()
    guild = inter.guild
    reason = "Превышено количество предупреждений"
    session.add(db.Warns(username=user.name,
                         end_date=datetime.datetime.now() + datetime.timedelta(days=warns['warns_duration']),
                         guild=guild.id))
    await inter.response.send_message(f"Пользователю {user.mention} было выдано предупреждение", ephemeral=True)
    if session.query(db.Warns).filter_by(username=user.name, guild=guild.id).count() == warns['max_warns']:
        session.query(db.Warns).filter_by(username=user.name, guild=guild.id).delete()
        await user.send(f"Вы были забанены на сервере {guild.name} по причине:\n{reason}")
        await inter.guild.ban(user, reason=reason)
        await inter.channel.send(f'Пользователь {user.mention} был забанен по причине:\n{reason}')
    session.commit()
    session.close()


@bot.slash_command(description='Снять предупреждение')
@commands.has_role(roles['moderators_role'])
async def unwarn(inter: disnake.ApplicationCommandInteraction, user: disnake.Member):
    guild = inter.guild
    session = db.Session()
    session.delete(session.query(db.Warns).filter_by(username=user.name, guild=guild.id).first())
    session.commit()
    session.close()
    await inter.response.send_message(f"Предупреждение с пользователя {user.mention} было снято", ephemeral=True)


@bot.slash_command(description='Список предупреждений')
async def warns(inter: disnake.ApplicationCommandInteraction):
    guild = inter.guild
    embed = disnake.Embed(title=f"Предупреждения", colour=16333380)
    embed.set_author(name=inter.author, icon_url=inter.author.display_avatar.url)
    session = db.Session()
    for warn in session.query(db.Warns).filter_by(username=inter.author.name, guild=guild.id).all():
        embed.add_field(name=f"Пользователь: {warn.username}",
                        value=f"Будет снято через: {warn.end_date - datetime.datetime.now()}", inline=False)
    if not embed.fields:
        embed.add_field(name="У вас пока нет предупреждений",
                        value="- И это превосходно, продолжайте в том же духе!",
                        inline=False)
    await inter.response.send_message(embed=embed)
    session.close()


@bot.slash_command(description='Список предупреждений')
@commands.has_role(roles['moderators_role'])
async def all_warns(inter: disnake.ApplicationCommandInteraction):
    guild = inter.guild
    session = db.Session()
    warns = session.query(db.Warns).filter_by(guild=guild.id).all()
    embed = disnake.Embed(title=f"Предупреждения", colour=16333380)
    embed.set_author(name=guild.owner, icon_url=guild.owner.display_avatar.url)
    for warn in warns:
        embed.add_field(name=f"Пользователь: {warn.username}",
                        value=f"Будет снято: {warn.end_date - datetime.datetime.now()}", inline=False)
    if not embed.fields:
        embed.add_field(name="На вашем сервере пока нет предупреждений",
                        value="- И это превосходно, продолжайте в том же духе!",
                        inline=False)
    await inter.response.send_message(embed=embed)
    session.close()


# Logs --------------------------------------------------------------------------------
@bot.event
async def on_message_delete(message: disnake.Message):
    log_channel = bot.get_channel(deleted_log_channel)
    if message.channel is not log_channel and message.channel is not bot.get_channel(report_channel):
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


# Reports ----------------------------------------------------------------------------------------
@bot.slash_command(description="Пожаловаться на пользователя")
async def report(inter: disnake.ApplicationCommandInteraction,
                 person: disnake.Member = disnake.Option('person', required=True),
                 reason: str = disnake.Option('reason', required=True)):
    report_found = False
    reports = bot.get_channel(report_channel)
    guild = inter.guild
    async for report_message in reports.history(limit=None):
        if f"Репорт на пользователя: {person}\nОт пользователя: {inter.author}" in report_message.content:
            report_found = True
            break
    if report_found:
        await inter.response.send_message("Репорт на данного пользователя уже был вами отправлен", ephemeral=True)
    else:
        if person == inter.author:
            await inter.response.send_message("Вы не можете зарепортить себя")
        else:
            report_text = f"Репорт на пользователя: {person.mention}\nОт пользователя: {inter.author.mention}\nПо причине: {reason}\nНа рассмотрение {guild.get_role(roles['moderators_role']).mention}"
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


# Autorole ---------------------------------------
@bot.event
async def on_member_join(member: disnake.Member):
    role = member.guild.get_role(roles['autorole_id'])
    await member.add_roles(role)


# Tickets -----------------------------------------------------------------
# Tickets message create
@bot.command()
@commands.has_role(roles['moderators_role'])
async def create_ticket_message(inter: disnake.MessageCommandInteraction):
    description = "Здесь вы можете создать тикет, для того чтобы задать вопрос касательно бота или сервера и получить ответ на него от модераторов сервера"
    embed = disnake.Embed(title='Создать тикет', description=description, colour=16333380)
    await inter.send(embed=embed, components=[
        disnake.ui.Button(label="Создать тикет", style=disnake.ButtonStyle.success, custom_id="create_ticket")
    ])
    await inter.message.delete()


# Buttons -----------------------------------------------------------------
@bot.listen("on_button_click")
async def help_listener(inter: disnake.MessageInteraction):
    # Tickets Buttons ---------------------------------------------------
    if inter.component.custom_id == "create_ticket":
        guild = inter.guild
        ticket_category = guild.get_channel(1160857669054242836)
        tickets = ticket_category.text_channels

        ticket_found = False
        for ticket in tickets:
            if ticket.name == f"ticket-{inter.author.id}":
                ticket_found = True
                break

        if ticket_found:
            await inter.response.send_message("Ошибка! Вы уже создали тикет.", ephemeral=True)
        else:
            overwrites = {
                inter.guild.default_role: disnake.PermissionOverwrite(view_channel=False),
                inter.author: disnake.PermissionOverwrite(view_channel=True),
                guild.get_role(roles['moderators_role']): disnake.PermissionOverwrite(view_channel=True)
            }
            await ticket_category.create_text_channel(f"ticket-{inter.author.id}", overwrites=overwrites)
            await inter.response.send_message("Тикет был успешно создан.", ephemeral=True)

            for new_ticket in ticket_category.text_channels:
                if new_ticket.name == f"ticket-{inter.author.id}":
                    text = "Тикет был успешно создан.\n" \
                           f"Автор тикета: {inter.author.mention}\n" \
                           f"Пользователи, имеющие доступ к ответу на тикет: {guild.get_role(roles['moderators_role']).mention}"
                    await new_ticket.send(text, components=[
                        disnake.ui.Button(label="Закрыть тикет", style=disnake.ButtonStyle.danger,
                                          custom_id="close_ticket")
                    ])

    if inter.component.custom_id == "close_ticket":
        role = inter.guild.get_role(roles['moderators_role'])
        if role in inter.author.roles:
            channel = bot.get_channel(inter.channel.id)
            await channel.delete()
        else:
            await inter.response.send_message("Похоже, у вас недостаточно прав для закрытия тикета", ephemeral=True)

    # Reports Buttons ---------------------------------------------
    if inter.component.custom_id == "close_report":
        await inter.message.delete()

    if inter.component.custom_id == "ban_report":
        guild = inter.guild
        reports = bot.get_channel(report_channel)
        message_lines = inter.message.content.split("\n")
        reported_user_id = int(message_lines[0].split()[-1][2:-1])
        reported_user = disnake.utils.get(guild.members, id=reported_user_id)
        reason = ' '.join(str(element) for element in message_lines[2].split()[2:])
        await reported_user.send(f"Вы были забанены на сервере {guild.name} по причине:\n{reason}")
        await inter.guild.ban(reported_user, reason=reason)
        await reports.send(f'Пользователь {reported_user.mention} был забанен по причине:\n{reason}')
        await inter.message.delete()

    if inter.component.custom_id == "mute_report":
        await inter.response.send_modal(MuteForm())

    if inter.component.custom_id == "warn_report":
        guild = inter.guild
        message_lines = inter.message.content.split("\n")
        reported_user_id = int(message_lines[0].split()[-1][2:-1])
        reported_user = disnake.utils.get(guild.members, id=reported_user_id)
        await warn(inter, user=reported_user)


# Voice channel creation --------------------------------------------------------------------------------
@bot.event
async def on_voice_state_update(member: disnake.Member, before, after):
    channel_id = voice_channel['channel_id']
    category_id = voice_channel['category_id']
    guild = member.guild
    category = guild.get_channel(category_id)
    muted = member.guild.get_role(roles['muted_role_id'])
    overwrites = {
        member: disnake.PermissionOverwrite(manage_channels=True),
        muted: disnake.PermissionOverwrite(speak=False, stream=False, send_messages=False)
    }

    if after.channel and after.channel.id == channel_id:
        vc = await guild.create_voice_channel(f"Канал {member.display_name}", overwrites=overwrites, category=category)
        await member.move_to(vc)

    if category and category.type == disnake.ChannelType.category:
        for channel in category.voice_channels:
            if not channel.members:
                await channel.delete()


# Bot start --------------------------------------------------------------------------------
@bot.event
async def on_ready():
    print("Бот успешно загружен.")
    db.create_tables()
    check_mutes.start()


bot.run(settings['token'])
