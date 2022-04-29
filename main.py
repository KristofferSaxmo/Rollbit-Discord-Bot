import discord
import os
import requests
import json
from discord.ext import tasks, commands

block = None
client = commands.Bot(command_prefix="$")
REMINDER_MSG = "There is now 1 BTC block left until the lottery starts"
JOIN_MSG = "Hi! Thank you for using this bot.\nPlease use the command **$setchannel** in the channel you wish to get reminded in.\nYou can also use **$timeleft** to get an estimated time until the lottery starts."


def get_block():
  global block
  response = requests.get("https://chain.so/api/v2/get_info/BTC")
  try:
    data = json.loads(response.text)
  except json.decoder.JSONDecodeError:
    print("Couldn't fetch block data from API")
    return block
  new_block = data["data"]["blocks"]
  return new_block


def add_json_data(data):
  guild_channel_pairs = get_json_data()

  guild_channel_pairs[list(data.keys())[0]] = list(data.values())[0]
  guild_channel_pairs = json.dumps(guild_channel_pairs, sort_keys=True, indent=4, separators=(",", ": "))

  with open(os.getcwd() + "/data.json", "w") as f:
    f.write(guild_channel_pairs)


def remove_json_data(guildID):
  guild_channel_pairs = get_json_data()
  for guild in guild_channel_pairs:
    if int(guild) == int(guildID):
      guild_channel_pairs.pop(guild)
      break 
  guild_channel_pairs = json.dumps(guild_channel_pairs, sort_keys=True, indent=4, separators=(",", ": "))
  with open(os.getcwd() + "/data.json", "w") as f:
    f.write(guild_channel_pairs)


def get_json_data():
  with open(os.getcwd() + "/data.json", "r") as f:
    return json.load(f)


@client.command()
@commands.cooldown(1, 10, commands.BucketType.user)
async def timeleft(ctx):
  global block
  remaining_blocks = 100 - (block - 30) % 100
  hours = (remaining_blocks * 10) // 60
  minutes = (remaining_blocks * 10) % 60
  msg = "There are " + str(remaining_blocks) + " blocks left, which takes approximately "
  if hours != 0:
    msg += str(hours) + " hours"
  if hours != 0 and minutes != 0:
    msg += " and "
  if minutes != 0:
    msg += str(minutes) + " minutes"
  await ctx.message.delete()
  await ctx.channel.send(content=msg, delete_after=60)


@client.command()
@commands.cooldown(1, 10, commands.BucketType.user)
@commands.has_permissions(administrator = True)
async def setchannel(ctx):
  dictionary = {str(ctx.guild.id): ctx.channel.id}
  add_json_data(dictionary)
  msg = "This channel has been set as the reminder channel"
  await ctx.message.delete()
  await ctx.channel.send(content=msg, delete_after=10)


@client.event
async def on_command_error(ctx, error):
  if isinstance(error, commands.CommandOnCooldown):
    msg = f"This command is on cooldown, you can use it again in {round(error.retry_after)} seconds"
    await ctx.message.delete()
    await ctx.channel.send(content=msg, delete_after=error.retry_after)


@client.event
async def on_guild_join(guild):
  print("Joined Guild:", guild.name)
  async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.bot_add):
    await entry.user.send(JOIN_MSG)


@client.event
async def on_guild_remove(guild):
  print("Left Guild:", guild.name)
  remove_json_data(guild.id)


@client.event
async def on_ready():
  print('We have logged in as {0.user}'.format(client))
  checkAPI.start()


@tasks.loop(seconds = 10)
async def checkAPI():
  global block
  if block == get_block():
    return
  block = get_block()
  remaining_blocks = 100 - (block - 30) % 100
  activity = str(remaining_blocks) + " blocks left"
  await client.change_presence(status=None, activity=discord.Game(activity))
  print("Remaining blocks:", remaining_blocks)
  if block % 100 == 29:
    guild_channel_pairs = get_json_data()
    for guild in guild_channel_pairs:
      channel = client.get_channel(guild_channel_pairs[guild])
      try:
        await channel.send(content=REMINDER_MSG, delete_after=600)
      except:
        remove_json_data(guild)
        print(f"Channel {channel.id} from guild {guild} could not be accessed. It has been removed from data.json")
  if block % 100 == 30:
    guild_channel_pairs = get_json_data()
    for guild in guild_channel_pairs:
      channel = client.get_channel(guild_channel_pairs[guild])
      try:
        await channel.send(content="The lottery has started", delete_after=300)
      except:
        remove_json_data(guild)
        print(f"Channel {channel.id} from guild {guild} could not be accessed. It has been removed from data.json")


client.run("TOKEN")