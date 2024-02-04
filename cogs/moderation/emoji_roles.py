import disnake
from disnake.ext import commands
from databases import db


class EmojiRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = db.Session()

    @commands.slash_command(description='Команда, добавляющая получение ролей по эмодзи к сообщению') # Команда, добавляющая получение ролей по эмодзи к сообщению
    @commands.has_permissions(administrator=True)
    async def add_emojiroles(self, inter: disnake.ApplicationCommandInteraction,
                            message_id: str = commands.Param(name='message_id',
                                                             description='Введите id сообщения, к которому нужно прикрепить эмодзи с ролями'),
                            roles: str = commands.Param(name='roles',
                                                        description='Поочередно через пробел введите id каждой роли, которую хотите прикрепить к сообщению'),
                            emojis: str = commands.Param(name='emojis',
                                                         description='Поочередно через пробел введите эмодзи, которые хотите прикрепить за каждой из ролей')):
        try:
            int(message_id)
        except TypeError:
            await inter.response.send_message('Неправильно введен id сообщения', ephemeral=True)
            return
        roles_list = []
        for role in roles.split():
            try:
                role = int(role)
            except TypeError:
                await inter.response.send_message('Неправильно введены роли', ephemeral=True)
                return
            roles_list.append(role)
        emojis_list = [emoji for emoji in emojis.split()]
        emoji_roles = dict(zip(roles_list, emojis_list))
        message = await inter.channel.fetch_message(message_id)
        for role, emoji in emoji_roles.items():
            self.session.add(db.EmojiRoles(guild=inter.guild.id, role=role, emoji=emoji))
            await message.add_reaction(emoji)
        self.session.commit()
        self.session.close()
        await inter.response.send_message('Эмодзи с ролями были успешно прикреплены к сообщению', ephemeral=True)


    @commands.slash_command(description='Команда, удаляющая эмодзи с ролями у сообщения') # Команда, удаляющая эмодзи с ролями у сообщения
    @commands.has_permissions(administrator=True)
    async def remove_emojiroles(self, inter: disnake.ApplicationCommandInteraction,
                               message_id: str = commands.Param(name='message_id',
                                                                description='Введите id сообщения, у которого нужно удалить эмодзи с ролями')):
        try:
            int(message_id)
        except TypeError:
            await inter.response.send_message('Неправильно введен id сообщения', ephemeral=True)
            return
        message = await inter.channel.fetch_message(message_id)
        emojis_list = [emoji for emoji in message.reactions]
        for emoji in emojis_list:
            self.session.query(db.EmojiRoles).filter_by(guild=inter.guild.id, emoji=emoji.emoji).delete()
            await message.clear_reaction(emoji)
        await inter.response.send_message(f'Эмодзи с ролями были успешно удалены', ephemeral=True)
        self.session.commit()
        self.session.close()


    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload): # Добавление ролей при добавлении эмодзи
        if payload.user_id == self.bot.user.id:
            return
        if payload.emoji.name in [emoji.emoji for emoji in self.session.query(db.EmojiRoles).filter_by(guild=payload.guild_id).all()]:
            guild = self.bot.get_guild(payload.guild_id)
            role_id = self.session.query(db.EmojiRoles).filter_by(guild=payload.guild_id, emoji=payload.emoji.name).first().role
            member = guild.get_member(payload.user_id)
            await member.add_roles(guild.get_role(role_id))

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload): # Удаление ролей при удалении эмодзи
        if payload.user_id == self.bot.user.id:
            return
        if payload.emoji.name in [emoji.emoji for emoji in self.session.query(db.EmojiRoles).filter_by(guild=payload.guild_id).all()]:
            guild = self.bot.get_guild(payload.guild_id)
            role_id = self.session.query(db.EmojiRoles).filter_by(guild=payload.guild_id, emoji=payload.emoji.name).first().role
            role = guild.get_role(role_id)
            member = guild.get_member(payload.user_id)
            if role in member.roles:
                await member.remove_roles(role)



def setup(bot):
    bot.add_cog(EmojiRoles(bot))
