import json
import requests
import discord

API_ENDPOINT = 'https://discord.com/api/v10'

with open('secrets.json') as f:
    secrets = json.load(f)

def get_token():
    data = {
        'grant_type': 'client_credentials',
        'scope': 'identify connections'
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    client_id = secrets['oauth2_client_id']
    client_secret = secrets['oauth2_client_secret']
    r = requests.post(f'{API_ENDPOINT}/oauth2/token', data=data, headers=headers, auth=(client_id, client_secret))
    r.raise_for_status()
    return r.json()['access_token']

# Create a function to send a message to the specified channel
def send_message_to_channel(channel_id, access_token, message):
    url = f"{API_ENDPOINT}/channels/{channel_id}/messages"
    headers = {
        "Authorization": f"Bot {access_token}",
        "Content-Type": "application/json"
    }
    data = {
        "content": message
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()

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

        # Log the message content to the console
        print(f"Received message: {message.type} `{message.content}`")

# Instantiate your custom client class
client = MyBot()

# Run the bot using your token
client.run(token)

# Call the function to send a message
#send_message_to_channel(channel_id, token, "Hello hackers!")
