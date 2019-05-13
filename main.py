from auth import bot_token
import re
import discord
from discord.ext import commands, buttons
from datetime import datetime
from dateutil import parser
from dateutil import tz
from dateutil.relativedelta import relativedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
sched = AsyncIOScheduler()
sched.start()

bot = commands.Bot(command_prefix = "/")

def parse_datetime(dt):
	compiled = re.compile("""(?:(?P<years>[0-9])(?:years?|y))?
                             (?:(?P<months>[0-9]{1,2})(?:months?|mo))?
                             (?:(?P<weeks>[0-9]{1,4})(?:weeks?|w))?
                             (?:(?P<days>[0-9]{1,5})(?:days?|d))?
                             (?:(?P<hours>[0-9]{1,5})(?:hours?|h))?
                             (?:(?P<minutes>[0-9]{1,5})(?:minutes?|m))?
                             (?:(?P<seconds>[0-9]{1,5})(?:seconds?|s))?
                             """, re.VERBOSE)

	match = compiled.fullmatch(dt)
	if match is None or not match.group(0):
		try:
			tzinfos = {"AEST": tz.gettz("Australia/Sydney")}
			dt = parser.parse(f"{dt} AEST", tzinfos=tzinfos)
			return dt
		except:
			return None

	data = { k: int(v) for k, v in match.groupdict(default=0).items() }
	now = datetime.now()
	dt = now + relativedelta(**data)
	return dt


class Reminder:
	def __init__(self, _datetime, msg, user, ctx, time, di):
		self._datetime = _datetime
		self.msg = msg
		self.user = user
		self.ctx = ctx
		self.time = time
		self.di = di
		sched.add_job(self.send_reminder, self.di, run_date=self._datetime)

	async def send_reminder(self):
		await Session(self._datetime, self.msg, self.user, self.ctx, self.time).start(page=await self.user.send(self.msg), ctx=self.ctx)


class Session(buttons.Session):
	def __init__(self, _datetime, msg, user, ctx, time):
		self._datetime = _datetime
		self.msg = msg
		self.user = user
		self.ctx = ctx
		self.time = time
		super().__init__(timeout=None, try_remove=True)


	async def parse_and_add_reminder(self, time):
		dt = parse_datetime(time)
		if dt == None:
			print('error resolving datetime')
			await self.user.send('error resolving datetime')
			return
		Reminder(dt, self.msg, self.user, self.ctx, self.time, 'date')
		await self.user.send('👍')

	@buttons.button('🔁', position=0)
	async def reschedule_reminder(self, ctx, member):
		await self.parse_and_add_reminder(self.time)

	@buttons.button('other:577312039576272897', position=1)
	async def choice_reschedule(self, ctx, member):
		await self.user.send('When?:')
		def check(m):
			return m.guild == None and m.author == member
		time = await bot.wait_for('message', check=check)
		await self.parse_and_add_reminder(time.content)

	@buttons.button('10_minutes:577312039689519124', position=2)
	async def ten_min_reschedule(self, ctx, member):
		await self.parse_and_add_reminder('10m')

	@buttons.button('30_minutes:577312039672872976', position=3)
	async def thirty_min_reschedule(self, ctx, member):
		await self.parse_and_add_reminder('30m')

	@buttons.button('1_hour:577312039702233088', position=4)
	async def one_hour_reschedule(self, ctx, member):
		await self.parse_and_add_reminder('1h')

	@buttons.button('2_hours:577312039517683763', position=5)
	async def two_hour_reschedule(self, ctx, member):
		await self.parse_and_add_reminder('2h')


@bot.command()
async def remindme(ctx, time, *, msg):
	user = ctx.message.author

	dt = parse_datetime(time)
	if dt == None:
		print('error resolving datetime')
		await ctx.send('error resolving datetime')
		return

	Reminder(dt, msg, user, ctx, time, 'date')
	await ctx.send("I'll remind you then!")

# @bot.command()
# async def reminder(ctx, interval, *, msg):
# 	user = ctx.message.author
#
# 	dt = parse_datetime(time)
# 	if dt == None:
# 		print('error resolving datetime')
# 		await ctx.send('error resolving datetime')
# 		return
#
# 	Reminder(dt, msg, user, ctx, time, 'interval')
# 	await ctx.send("I'll remind you then!")


@bot.event
async def on_ready():
	print("Logged in!\n----------\n")
	print(f"Connected to {len(bot.guilds)} guilds...  {', '.join([e.name for e in bot.guilds])}")

bot.run(bot_token)