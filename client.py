
# Import required libraries
import discord, os
import threading

class Client(discord.Client):
    
    channel: discord.TextChannel = None

    async def upload(self, database: dict, filename: str, parts: list[bytes]):
        """Uploads `parts` to Discord and assigns the list of URLs generated
        to `database[filename]`."""

        temp_file = f"tmp-{filename}"
        for i in range(len(parts)):
            with open(temp_file, "wb") as f:
                f.write(parts[i])

            message = await self.channel.send(
                file = discord.File(temp_file, f"{filename}{('-' + str(i)) if i > 0 else ''}")
            )
            parts[i] = message.attachments[0].url
            os.remove(temp_file)

        database[filename] = parts

def run(channel_id: str, token: str) -> Client:
    "Creates a new client and runs it in a separate thread."

    client = Client(
        intents=discord.Intents.all())

    @client.event
    async def on_ready():
        client.channel = await client.fetch_channel(channel_id)
        if not client.channel:
            exit(1)

    bot_thread = threading.Thread(target=lambda : client.run(token))
    bot_thread.daemon = True
    bot_thread.start()

    return client

