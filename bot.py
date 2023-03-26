import json
import openai
import discord

API_ENDPOINT = 'https://discord.com/api/v10'

with open('secrets.json') as f:
    secrets = json.load(f)

openai.api_key = secrets['openai_key']
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

        msg = message.content
        if msg.startswith('!gpt '):
            reply = openai.ChatCompletion.create(model="gpt-4", messages = [
                    {"role": "user", "content": msg}
            ])
            print(json.dumps(reply, indent=4))
            #await message.channel.send(json.dumps(reply))

# Instantiate your custom client class
client = MyBot()

# Run the bot using your token
client.run(token)
