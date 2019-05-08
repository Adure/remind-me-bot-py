from auth import bot_token
import re
import discord
from discord.ext import commands, buttons
from datetime import datetime
from dateutil import parser
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
			dt = parser.parse(dt)
			return dt
		except:
			return None

	data = { k: int(v) for k, v in match.groupdict(default=0).items() }
	now = datetime.now()
	dt = now + relativedelta(**data)
	return dt


class Reminder:
	def __init__(self, _datetime, msg, user, ctx, time):
		self._datetime = _datetime
		self.msg = msg
		self.user = user
		self.ctx = ctx
		self.time = time
		sched.add_job(self.send_reminder, 'date', run_date=self._datetime)

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

	@buttons.button('🔁')
	async def reschedule_reminder(self, ctx):
		dt = parse_datetime(self.time)
		Reminder(dt, self.msg, self.user, self.ctx, self.time)


@bot.command()
async def remindme(ctx, time, *, msg):
	user = ctx.message.author

	# Get due datetime
	dt = parse_datetime(time)
	if dt == None:
		print('error resolving datetime')
		await ctx.send('error resolving datetime')
		return

	# Create reminder to run at the given time, with the given message
	Reminder(dt, msg, user, ctx, time)
	await ctx.send("I'll remind you then!")

@bot.event
async def on_ready():
	print("Ready!")

bot.run(bot_token)