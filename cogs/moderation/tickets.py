import disnake
from disnake.ext import commands
from databases import db


class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = db.Session()

    @commands.slash_command(description="Создать сообщение, при помощи которого будут создаваться тикеты")
    @commands.has_permissions(administrator=True)
    async def create_ticket_message(self, inter: disnake.ApplicationCommandInteraction): # Команда для создания сообщения, при помощи которого будут создаваться тикеты
        description = "Здесь вы можете создать тикет, для того чтобы задать вопрос касательно бота или сервера и получить ответ на него от модераторов сервера"
        embed = disnake.Embed(title='Создать тикет', description=description, colour=16333380)
        await inter.send(embed=embed, components=[
            disnake.ui.Button(label="Создать тикет", style=disnake.ButtonStyle.success, custom_id="create_ticket")
        ])

    @commands.Cog.listener()
    async def on_button_click(self, inter: disnake.MessageInteraction):
        if inter.component.custom_id == "create_ticket": # Нажатие на кнопку создания тикетов
            guild = inter.guild
            if self.session.query(db.Configs).filter_by(guild=guild.id).first().tickets_category_id is not None:
                ticket_category = guild.get_channel(
                    self.session.query(db.Configs).filter_by(guild=guild.id).first().tickets_category_id)
            else:
                ticket_category = await guild.create_category_channel("Тикеты", overwrites={
                    guild.default_role: disnake.PermissionOverwrite(view_channel=False)})
                self.session.query(db.Configs).filter_by(guild=guild.id).update(
                    {db.Configs.tickets_category_id: ticket_category.id})
                self.session.commit()
                self.session.close()

            for ticket in ticket_category.text_channels:
                if ticket.name == f"ticket-{inter.author.id}":
                    await inter.response.send_message("Ошибка! Вы уже создали тикет.", ephemeral=True)
                else:
                    overwrites = {
                        inter.guild.default_role: disnake.PermissionOverwrite(view_channel=False),
                        inter.author: disnake.PermissionOverwrite(view_channel=True),
                        guild.owner: disnake.PermissionOverwrite(view_channel=True)
                    }
                    await ticket_category.create_text_channel(f"ticket-{inter.author.id}", overwrites=overwrites)
                    await inter.response.send_message("Тикет был успешно создан.", ephemeral=True)

                    for new_ticket in ticket_category.text_channels:
                        if new_ticket.name == f"ticket-{inter.author.id}":
                            text = "Тикет был успешно создан.\n" \
                                   f"Автор тикета: {inter.author.mention}\n" \
                                   f"Пользователи, имеющие доступ к ответу на тикет: {guild.owner.mention}"
                            await new_ticket.send(text, components=[
                                disnake.ui.Button(label="Закрыть тикет", style=disnake.ButtonStyle.danger,
                                                  custom_id="close_ticket")
                            ])

        if inter.component.custom_id == "close_ticket": # Нажатие на кнопку закрытия тикетов
            guild = inter.guild
            if inter.author is guild.owner:
                channel = self.bot.get_channel(inter.channel.id)
                await channel.delete()
            else:
                await inter.response.send_message("Похоже, у вас недостаточно прав для закрытия тикета", ephemeral=True)


def setup(bot):
    bot.add_cog(Tickets(bot))
