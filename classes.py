import disnake
from disnake.ext import commands
import random
from dbconnect import eccur, economy

class DropdownJobs(disnake.ui.StringSelect):
    def __init__(self, inter):
        self.person = inter.author.id

        eccur.execute("SELECT id, name, lvl, salary FROM works_%s" % (inter.guild.id))
        options = []
        jobs = list(eccur.fetchall())
        for n in jobs:
            options.append(disnake.SelectOption(label=n[1], description=f"[Уровень - {n[2]}] [Зарплата - {n[3]}]"))

        super().__init__(placeholder="Выбор работы",
                         min_values=1,
                         max_values=1,
                         options=options)

    async def callback(self, inter:disnake.MessageInteraction):
        if self.person == inter.author.id:
            person = eccur.execute("SELECT lvl FROM members_%s WHERE id = ?" % (inter.guild.id), (inter.author.id,)).fetchone()[0]
            job = eccur.execute("SELECT id, lvl, roaster FROM works_%s WHERE name = ?" % (inter.guild.id), (self.values[0],)).fetchone()
            if job[2] is not None:
                if job[2] <= eccur.execute("SELECT COUNT(job) FROM members_%s WHERE job = ?" % (inter.guild.id), (job[0],)).fetchone()[0]:
                    await inter.response.edit_message("На данной работе уже работает максимальное количество человек", view=None)
                    return
            if person >= job[1]:
                eccur.execute("UPDATE members_%s SET job = ? WHERE id = ?" % (inter.guild.id), (job[0], inter.author.id))
                economy.commit()
                await inter.response.edit_message(f"{inter.author.mention} устроился на работу %s" % (self.values[0]), view = None)
            else:
                await inter.response.edit_message("Недостаточный уровень чтобы устроиться на работу", view = None)
        else: await inter.response.send_message("Вы не вызывали jobs", ephemeral=True)


class DropdownViewJobs(disnake.ui.View):
    def __init__(self,inter):
        super().__init__()

        self.add_item(DropdownJobs(inter))

class BuyItemView(disnake.ui.View):
    def __init__(self, item, orig):
        self.orig = orig
        self.item = item
        super().__init__()

    @disnake.ui.button(label="Купить", style=disnake.ButtonStyle.green)
    async def confirm_button(self, button, inter):

        if self.orig == inter.author.name:
            person = eccur.execute("SELECT lvl, bank FROM members_%s WHERE id = ?" % (inter.guild.id), (inter.author.id,)).fetchone()
            if self.item[3] > person[0]:
                await inter.response.edit_message("Слишком маленький уровень!", view=None)
                return
            if self.item[2] > person[1]:
                await inter.response.edit_message("Недостаточно средств!", view=None)
                return
            if self.item[4] == "2":
                text = self.item[5].split("<>")
                await inter.response.edit_message(text[random.randint(0, len(text)-1)], view=None)
            elif self.item[4] == "1":
                role = disnake.utils.get(inter.guild.roles, id=int(self.item[5]))
                await inter.author.add_roles(role)
                await inter.response.edit_message(f"Теперь вы {role}", view=None)
            elif self.item[4] == "3":
                eccur.execute("UPDATE members_%s SET expa = (expa + ?) WHERE id = ?" % (inter.guild.id), (self.item[5], inter.author.id,))
                eccur.execute("SELECT lvl, expa FROM members_%s WHERE id = ?" % (inter.guild.id), (inter.author.id,))
                per = eccur.fetchone()
                await inter.response.send_message(f"У вас {per[1]} опыта, {per[0]} уровень")

            eccur.execute("UPDATE members_%s SET bank = ? WHERE id = ?" % (inter.guild.id), (person[1] - self.item[2], inter.author.id,))
            economy.commit()
        else: await inter.response.send_message("Вы не покупатель", ephemeral=True)


    @disnake.ui.button(label="Отменить", style=disnake.ButtonStyle.red)
    async def decline_button(self, button, inter):
        if self.orig == inter.author.name:
            await inter.response.edit_message("Ждем вас в следующий раз!", view=None)
        else:
            await inter.response.send_message("Вы не покупатель", ephemeral=True)
