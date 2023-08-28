import asyncio
import disnake
from disnake.ext import commands
import datetime
from classes import BuyItemView, DropdownViewJobs
from dbconnect import eccur, economy


class Economy(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            try:
                eccur.execute("INSERT INTO servers(id, name, work_exp, game_exp) VALUES (?,?,15,3)", (guild.id, guild.name,))
            except:
                pass
            try:
                eccur.execute('''CREATE TABLE members_%s (
                                                    id      INTEGER NOT NULL UNIQUE,
                                                    bank	INTEGER NOT NULL,
                                                    lvl	    INTEGER NOT NULL,
                                                    expa    INTEGER NOT NULL,
                                                    job     TEXT,
                                                    job_time TEXT,
                                                    PRIMARY KEY("id"))''' % (guild.id))
            except:
                pass
            try:
                eccur.execute('''CREATE TABLE works_%s (
                                                    id      INTEGER NOT NULL UNIQUE,
                                                    name	TEXT NOT NULL,
                                                    lvl	    INTEGER NOT NULL,
                                                    salary  INTEGER NOT NULL,
                                                    roaster INTEGER,
                                                    PRIMARY KEY("id" AUTOINCREMENT))''' % (guild.id))
            except:
                pass
            try:
                eccur.execute('''CREATE TABLE shop_%s (
                                                    id      INTEGER NOT NULL UNIQUE,
                                                    name    TEXT NOT NULL,
                                                    type    TEXT NOT NULL,
                                                    value   TEXT NOT NULL,
                                                    cost    INTEGER NOT NULL,
                                                    lvl     INTEGER,
                                                    PRIMARY KEY("id" AUTOINCREMENT))''' % (guild.id))
            except:
                pass
            try:
                for member in guild.members:
                    eccur.execute("INSERT INTO members_%s(id, bank, lvl, expa) VALUES (?,0,0,0)" % (guild.id),
                                  (member.id,))
            except:
                pass
            economy.commit()


    @commands.Cog.listener()
    async def on_guild_join(self, guild: disnake.Guild):
        try:
            eccur.execute("INSERT INTO servers(id, name, work_exp, game_exp) VALUES (?,?,15,3)", (guild.id, guild.name,))
        except:
            pass
        try:
            eccur.execute('''CREATE TABLE members_%s (
                                                id      INTEGER NOT NULL UNIQUE,
                                                bank	INTEGER NOT NULL,
                                                lvl	    INTEGER NOT NULL,
                                                expa    INTEGER NOT NULL,
                                                job     TEXT,
                                                job_time TEXT,
                                                PRIMARY KEY("id"))''' % (guild.id))
        except:
            pass
        try:
            eccur.execute('''CREATE TABLE works_%s (
                                                id      INTEGER NOT NULL UNIQUE,
                                                name	TEXT NOT NULL,
                                                lvl	    INTEGER NOT NULL,
                                                salary  INTEGER NOT NULL,
                                                roaster INTEGER,
                                                PRIMARY KEY("id" AUTOINCREMENT))''' % (guild.id))
        except:
            pass
        try:
            eccur.execute('''CREATE TABLE shop_%s (
                                                id      INTEGER NOT NULL UNIQUE,
                                                name    TEXT NOT NULL,
                                                type    TEXT NOT NULL,
                                                value   TEXT NOT NULL,
                                                cost    INTEGER NOT NULL,
                                                lvl     INTEGER,
                                                PRIMARY KEY("id" AUTOINCREMENT))''' % (guild.id))
        except:
            pass
        try:
            for member in guild.members:
                eccur.execute("INSERT INTO members_%s(id, bank, lvl, expa) VALUES (?,0,0,0)" % (guild.id),
                              (member.id,))
        except:
            pass
        economy.commit()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        eccur.execute("INSERT INTO members_%s(id, bank, lvl, expa) VALUES (?,0,0,0)" % member.guild.id, (member.id,))
        economy.commit()

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        eccur.execute("DELETE FROM members_%s WHERE id = ?" % member.guild.id, (member.id,))
        economy.commit()

    @commands.Cog.listener()
    async def on_slash_command_completion(self, inter):
        await asyncio.sleep(3)
        eccur.execute("SELECT lvl, expa FROM members_%s WHERE id = ?" % inter.guild.id, (inter.author.id,))
        stats = list(eccur.fetchone())
        check = ((20 + (stats[0] * 5)) + (10 * stats[0]))   # (( 20 + (person_lvl * 5)) + (10 * person_lvl)) - how much require exp for next lvl
                                                            #                                       сколько опыта требуется до следующего уровня
        while stats[1] >= check:
            stats[1] -= check
            stats[0] += 1
            eccur.execute("UPDATE members_%s SET lvl = ?, expa = ? WHERE id = ?" % inter.guild.id,
                          (stats[0], stats[1], inter.author.id,))
            economy.commit()
            await inter.channel.send(f"{inter.author.mention} повышен до {stats[0]} уровня!")
        else:
            return

    @commands.slash_command(description="Добавить новую работу")
    @commands.has_permissions(administrator=True)
    async def add_job(self, inter, *, name: str = commands.Param(max_length=16),
                      lvl: int= commands.Param(min_value=0),
                      salary: int = commands.Param(min_value=0),
                      roaster=None):
        eccur.execute("INSERT INTO works_%s(name, lvl, salary, roaster) VALUES (?,?,?,?)" % inter.guild.id,
                      (name, lvl, salary, roaster))
        economy.commit()
        await inter.response.send_message("Работа добавлена - %s" % name, ephemeral=True)

    @commands.slash_command(description="Удалить работу")
    @commands.has_permissions(administrator=True)
    async def del_job(self, inter, *,
                      name: str = commands.Param(description="Название работы, полностью")):
        id = eccur.execute("SELECT id FROM works_%s WHERE name = ?" % inter.guild.id, (name,)).fetchone()
        if id is None:
            await inter.response.send_message("Такой профессии нет, повторите попытку")
        else:
            eccur.execute("UPDATE members_%s SET job = ? WHERE job = ?" % (inter.guild.id), (None, id[0],))
            eccur.execute("DELETE FROM works_%s WHERE name = ?" % inter.guild.id, (name,))
            economy.commit()
            await inter.response.send_message(f"{name} удалена", ephemeral=True)

    @commands.slash_command(description="Работать")
    async def work(self, inter):
        person = inter.author.id
        guild = inter.guild.id
        eccur.execute("SELECT job, job_time, bank, expa FROM members_%s WHERE id = ?" % guild, (person,))
        worker = list(eccur.fetchone())
        if worker[0] == None:
            await inter.response.send_message("Сначала устройтесь на работу", ephemeral=True)
            return
        elif worker[1] == str(datetime.date.today()):
            await inter.response.send_message("Вы уже работали сегодня! Приходите завтра!", ephemeral=True)
            return
        else:
            job = eccur.execute("SELECT salary FROM works_%s WHERE id = ?" % (guild), (worker[0],)).fetchone()[0]
            worker[2] += job
            worker[3] += eccur.execute("SELECT work_exp FROM servers WHERE id = ?", (inter.guild.id,)).fetchone()[0]
            eccur.execute("UPDATE members_%s SET job_time = ?, bank = ?, expa = ? WHERE id = ?" % (guild),
                          (datetime.date.today(), worker[2], worker[3], person,))
            economy.commit()
            await inter.response.send_message("Вы заработали - %s монет" % (job))

    @commands.slash_command(description="Устроиться на работу")
    async def jobs(self, inter):
        await inter.response.send_message("Выберите желаемую профессию", view=DropdownViewJobs(inter))

    @commands.slash_command(description="Узнать свой баланс")
    async def balance(self, inter):
        eccur.execute("SELECT bank FROM members_%s WHERE id = ?" % (inter.guild.id), (inter.author.id,))
        await inter.response.send_message("Ваш баланс: %s" % (eccur.fetchone()[0]))

    @commands.slash_command(description="Узнать уровень")
    async def stats(self, inter):
        eccur.execute("SELECT lvl, expa FROM members_%s WHERE id = ?" % (inter.guild.id), (inter.author.id,))
        stats = eccur.fetchone()
        await inter.response.send_message(
            f"Уровень - {stats[0]}, опыт - {stats[1]}\nДо следующего уровня осталось {((20 + (stats[0] * 5)) + (10 * stats[0])) - stats[1]} опыта")

    @commands.slash_command(description="Изменить количество денег")
    @commands.has_permissions(administrator=True)
    async def set_balance(self, inter, money, member: disnake.Member = None):
        if member == None:
            member = inter.author
        eccur.execute("UPDATE members_%s SET bank = ? WHERE id = ?" % (inter.guild.id), (money, member.id,))
        economy.commit()
        await inter.response.send_message(f"{member.mention} был изменен баланс на {money}")

    @commands.slash_command(description="Изменить уровень")
    @commands.has_permissions(administrator=True)
    async def set_lvl(self, inter, lvl, member: disnake.Member = 0):
        if member == 0:
            member = inter.author
        eccur.execute("UPDATE members_%s SET lvl = ? WHERE id = ?" % (inter.guild.id), (lvl, member.id,))
        economy.commit()
        await inter.response.send_message(f"{member.mention} был изменен уровень на {lvl}")

    @commands.slash_command(description="Изменить получаемый опыт за работу")
    @commands.has_permissions(administrator=True)
    async def set_work_exp(self, inter, exp: int = commands.Param(min_value=0)):
        eccur.execute("UPDATE servers SET work_exp = ? WHERE id = ?", (exp, inter.guild.id,))
        economy.commit()
        await inter.response.send_message(f"Опыт за работу был изменен на {exp}")

    @commands.slash_command(description="Изменить получаемый опыт за игры")
    @commands.has_permissions(administrator=True)
    async def set_game_exp(self, inter, exp: int = commands.Param(min_value=0)):
        eccur.execute("UPDATE servers SET game_exp = ? WHERE id = ?", (exp, inter.guild.id,))
        economy.commit()
        await inter.response.send_message(f"Опыт за игры был изменен на {exp}")

    @commands.slash_command(description="Добавить позицию в магазин")
    @commands.has_permissions(administrator=True)
    async def add_shop(self, inter, name: str = commands.Param(max_length=16, description="Отображаемое имя товара"),
                       type: str = commands.Param(choices=["role", "text", "expa"],
                                                  description="Тип товара: роль, текст, опыт"), *,
                       item: str = commands.Param(
                           description="Для случайных фраз используйте **<>** между ними Для роли - упомяните ее Для опыта - введите число"),
                       cost: int = commands.Param(min_value=0), lvl: int = 0):
        if type == "role":
            type = 1
        elif type == "text" or type == "imag":
            type = 2
        elif type == "expa":
            type = 3
        else:
            await inter.response.send_message("Доступные типы: role, text, expa. (Роль, текст, изображение)")
            return
        if type == 1:
            role = item[3:-1]
            eccur.execute("INSERT INTO shop_%s(name, value, type, cost, lvl) VALUES (?,?,?,?,?)" % (inter.guild.id),
                          (name, role, type, cost, lvl))
        elif type == 2:
            eccur.execute("INSERT INTO shop_%s(name, value, type, cost, lvl) VALUES (?,?,?,?,?)" % (inter.guild.id),
                          (name, item, type, cost, lvl))
        elif type == 3:
            eccur.execute("INSERT INTO shop_%s(name, value, type, cost, lvl) VALUES (?,?,?,?,?)" % (inter.guild.id),
                          (name, item, type, cost, lvl))
        await inter.response.send_message(f"{name} добавлен", ephemeral=True)
        economy.commit()

    @commands.slash_command(description="Удалить предмет из магазина")
    @commands.has_permissions(administrator=True)
    async def del_shop(self, inter, name: str = commands.Param(description="имя товара")):
        eccur.execute("DELETE FROM shop_%s WHERE name = ?" % (inter.guild.id), (name,))
        economy.commit()
        await inter.response.send_message("Удалено", ephemeral=True)

    @commands.slash_command(description="Магазин")
    async def shop(self, inter):
        items = eccur.execute("SELECT id, name, cost FROM shop_%s" % (inter.guild.id)).fetchall()
        texto = str()
        for i, n in enumerate(items):
            texto += f"{i + 1}) {n[1]} - {n[2]} монет\n"
        texto += "\nКакой предмет вас заинтересовал? (Напишите название предмета)"
        await inter.response.send_message(texto, delete_after=60)

        def check(m):
            return m.author == inter.author

        try:
            answer = await self.bot.wait_for('message', timeout=60.0, check=check)
            n = eccur.execute("SELECT id, name, cost, lvl, type, value FROM shop_%s WHERE name = ?" % (inter.guild.id),
                              (answer.content,)).fetchone()
            texto = f"{inter.author.mention}\n{n[1]} - {n[2]} монет\nДоступен после {n[3]} уровня"

            await inter.channel.send(texto, view=BuyItemView(n, inter.author.name))
        except:
            await inter.send("Время вышло", delete_after=10)

    @commands.slash_command(description="Передать деньги")
    async def give_money(self, inter, money: int, member: disnake.Member):
        eccur.execute("SELECT bank FROM members_%s WHERE id = ?" % (inter.guild.id), (inter.author.id,))
        if money > eccur.fetchone()[0]:
            await inter.response.send_message("Недостаточно денег для перевода", ephemeral=True)
            return
        if member == None:
            member = inter.author
        eccur.execute("UPDATE members_%s SET bank = (bank + ?) WHERE id = ?" % (inter.guild.id), (money, member.id,))
        eccur.execute("UPDATE members_%s SET bank = (bank - ?) WHERE id = ?" % (inter.guild.id),
                      (money, inter.author.id,))
        economy.commit()
        await inter.response.send_message(f"{member.mention} получил {money} монет от {inter.author.mention}")


def setup(bot: commands.Bot):
    bot.add_cog(Economy(bot))
