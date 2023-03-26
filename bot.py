import json
import requests
import discord

API_ENDPOINT = 'https://discord.com/api/v10'

with open('secrets.json') as f:
    secrets = json.load(f)

token = secrets['bot_token']
channel_id = secrets['discord_channel_id']

class MyBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents(messages=True, message_content=True))

    async def on_ready(self):
        print(f"We have logged in as {self.user}")

    async def on_message(self, message):
        # Don't respond to messages from the bot itself
        if message.author == self.user:
            return

        if message.type != discord.MessageType.default:
            return

        if str(message.channel.id) != channel_id:   # Only listen to the given channel
            return

        # Log the message content to the console
        print(f"Received message: {message.type} `{message.content}`")
        await message.channel.send('gotcha')

# Instantiate your custom client class
client = MyBot()

# Run the bot using your token
client.run(token)
