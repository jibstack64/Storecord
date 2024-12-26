
# Import required libraries
import os
import sys
import discord
import json

client = discord.Client(
    intents=discord.Intents.all())

# Load database
try:
    database = json.load(open("database.json", "r"))
except json.JSONDecodeError:
    print("The database file is not formatted correctly.")
    exit(1)
except FileNotFoundError:
    database = {}

# Load token
if len(sys.argv) < 2:
    print("No token provided.")
    exit(1)
TOKEN = sys.argv[1]
PREFIX = "" # This is given a value in on_ready

@client.event
async def on_ready():
    global PREFIX
    PREFIX = f"<@{client.user.id}>"
    print("Connected.")

@client.event
async def on_message(message: discord.Message):

    if message.channel.guild != None:
        return

    # Add sent attachments to the database
    if len(message.attachments) > 0:
        for attachment in message.attachments:
            if attachment.url not in list(database.values()):
                filename = os.path.basename(attachment.url).split("?")[0]
                database[filename] = attachment.url
                await message.channel.send(f"+ `{filename}`")

    if not message.content.startswith(PREFIX):
        return
    
    # Commands
    command = message.content[len(PREFIX):].strip().split(" ")
    command, args = command[0], command[1:]
    if command == "list":
        if len(args) > 0:
            return await message.reply("Invalid command format.")
        if len(database) == 0:
            return await message.reply("No files to list.")
        for name, url in database.items():
            await message.channel.send(embed=discord.Embed(
                title="",
                description=f"[{name}]({url})"
            ))
    elif command == "show":
        if len(args) > 1:
            return await message.reply("Invalid command format.")
        url = database.get(args[0], None)
        if url == None:
            return await message.reply("File not found.")
        await message.reply(f"`{args[0]}`:", file=discord.File(url))
    else:
        return await message.reply("Invalid command.")

    return
        

client.run(TOKEN)
json.dump(database, open("database.json", "w"), indent=4)
