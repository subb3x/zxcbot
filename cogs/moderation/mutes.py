import disnake
from disnake.ext import commands, tasks
from databases import db
import datetime
from main import PersistentViewBot


async def mute_func(bot, inter, user: disnake.Member, duration: str):
    session = db.Session()
    guild = inter.guild
    muted_role = session.query(db.Configs).filter(db.Configs.guild == guild.id).first().muted_role_id
    if muted_role is None:
        muted_role = await bot.create_role(guild, name='Замучен', hoist=False, mentionable=False,
                                                color='#000000')
        await bot.edit_role_positions({muted_role: -2})
        await muted_role.edit(permissions=disnake.Permissions(speak=False, send_messages=False))
        session.add(db.Configs(guild=guild.id, muted_role_id=muted_role))
        session.commit()
        session.close()
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
    session.add(db.Mutes(user=user.id,
                         end_date=datetime.datetime.now() + datetime.timedelta(minutes=minutes,
                                                                               hours=hours,
                                                                               days=days),
                         guild=guild.id))
    session.commit()
    session.close()
    await user.add_roles(guild.get_role(muted_role))
    if user.voice:
        previous_channel = user.voice.channel
        mute_reconnect = session.query(db.Configs).filter(
            db.Configs.guild == guild.id).first().mute_reconnect_id
        await user.move_to(channel=guild.get_channel(mute_reconnect))
        await user.move_to(previous_channel)
    await inter.response.send_message(f"Пользователь {user.mention} был замучен на {duration}",
                                      ephemeral=True)
    try:
        await inter.message.delete()
    except AttributeError:
        pass


class Mutes(commands.Cog):

    def __init__(self, bot: PersistentViewBot):
        self.bot = bot
        self.session = db.Session()
        bot.loop.create_task(self.on_ready())

    async def on_ready(self):
        await self.bot.wait_until_ready()
        self.check_mutes.start()

    class MuteForm(disnake.ui.Modal):  # Форма для мута через кнопку в репортах
        def __init__(self, bot):
            components = [
                disnake.ui.TextInput(
                    label="Длительность мута",
                    custom_id="mute_duration"
                )
            ]
            self.bot = bot
            super().__init__(title="Длительность мута", components=components)

        async def callback(self, inter: disnake.ModalInteraction):
            guild = inter.guild
            message_lines = inter.message.content.split("\n")
            reported_user_id = int(message_lines[0].split()[-1][2:-1])
            reported_user = disnake.utils.get(guild.members, id=reported_user_id)
            mute_duration = inter.text_values.get("mute_duration")
            await inter.message.delete()
            await mute_func(bot=self.bot,inter=inter, user=reported_user, duration=mute_duration)

    @commands.slash_command(description='Выдать мут') # Команда для выдачи мута юзеру
    @commands.has_permissions(mute_members=True)
    async def mute(self, inter: disnake.ApplicationCommandInteraction,
                   user: disnake.Member = commands.Param(name="user", description="Пользователь"),
                   duration: str = commands.Param(name="duration",
                                                  description="Длительность мута")):
        await mute_func(bot=self.bot, inter=inter, user=user, duration=duration)

    @commands.slash_command(description='Снять мут') # Команда для снятия мута с пользователя
    @commands.has_permissions(mute_members=True)
    async def unmute(self, inter: disnake.ApplicationCommandInteraction, user: disnake.Member = commands.Param(
        name="user", description="Пользователь")):
        guild = inter.guild
        muted_role = self.session.query(db.Configs).filter(db.Configs.guild == guild.id).first().muted_role_id
        mute_reconnect = self.session.query(db.Configs).filter(db.Configs.guild == guild.id).first().mute_reconnect_id

        self.session.query(db.Mutes).filter(db.Mutes.user == user.id).delete()
        self.session.commit()
        self.session.close()

        await user.remove_roles(muted_role)
        if user.voice:
            previous_channel = user.voice.channel
            await user.move_to(channel=guild.get_channel(mute_reconnect))
            await user.move_to(previous_channel)
        await inter.response.send_message(f"Пользователь {user.mention} был размучен", ephemeral=True)

    @tasks.loop(seconds=10)
    async def check_mutes(self): # Каждые 10 секунд проверяет, истекли ли муты, и размучивает если истекли
        for muted_user in self.session.query(db.Mutes).filter(db.Mutes.end_date < datetime.datetime.now()).all():
            guild_id = self.session.query(db.Mutes).filter(db.Mutes.guild == muted_user.guild).first().guild
            guild = self.bot.get_guild(guild_id)
            user = guild.get_member(muted_user.user)
            muted_role = self.session.query(db.Configs).filter(db.Configs.guild == guild_id).first().muted_role_id
            mute_reconnect = self.session.query(db.Configs).filter(
                db.Configs.guild == guild_id).first().mute_reconnect_id
            self.session.delete(muted_user)
            await user.remove_roles(guild.get_role(muted_role))
            if user.voice:
                previous_channel = user.voice.channel
                await user.move_to(channel=guild.get_channel(mute_reconnect))
                await user.move_to(previous_channel)
        self.session.commit()
        self.session.close()
    @commands.Cog.listener()
    async def on_button_click(self, inter: disnake.MessageInteraction):
        if inter.component.custom_id == "mute_report":  # Кнопка, отправляющая форму для мута зарепорченного пользователя
            await inter.response.send_modal(Mutes.MuteForm(bot=self.bot))


def setup(bot):
    bot.add_cog(Mutes(bot))
