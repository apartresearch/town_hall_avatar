import json
import openai
import discord
import os
import random

API_ENDPOINT = 'https://discord.com/api/v10'

with open('secrets.json') as f:
    secrets = json.load(f)

openai.api_key = secrets['openai_key']
token = secrets['bot_token']
channel_id = secrets['discord_channel_id']

class MyBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents(messages=True, message_content=True))
        self.avatars = []
        self.introductions = {}
        self.topic = None
        self.conversation = [
            {"role":"system","content":"You are TownHallBot. Your role is to predict what different people will say on a given topic. Feel free to make the characters assertive and the conversations spicy!"}
        ]
        self.next_message = ''
        i = 0
        while True:
            self.state_file = f'state{i}.json'
            self.state_i = i
            if not os.path.exists(self.state_file):
                break
            i += 1

    async def on_ready(self):
        print(f"We have logged in as {self.user}")

    def add_avatar(self, name, introduction):
        print(f"ADD_AVATAR {name} {introduction}")
        if name in self.avatars:
            raise ValueError(f"Name {name} already exists")
        self.next_message += f"A new person has joined the discussion, called {name}. {introduction}\n\n"
        self.avatars.append(name)
        self.introductions[name] = introduction

    def set_topic(self, topic):
        print(f"SET_TOPIC {topic}")
        if self.topic is None:
            self.next_message += f'The topic is: {topic}.\n\n'
        else:
            self.next_message += f'The topic has been changed to: {topic}.\n\n'
        self.topic = topic

    def append_message(self, author, msg):
        if '"' in msg:
            raise ValueError("Message contains doublequote")
        self.next_message += f'{author} says "{msg}".\n\n'

    def random_avatar(self):
        return random.choice(self.avatars)

    def get_avatar_reply(self, avatars):
        avatar_list = ' and '.join(random.sample(avatars, k=len(avatars)))
        self.next_message += f'What would {avatar_list} say on the topic, in one sentence per person?'
        reply = self._flush()
        return reply

    def _flush(self):
        self.conversation.append({"role":"user", "content":self.next_message})
        self.next_message = ''
        print("==== SENDING TO OPENAI ====\n")
        print(json.dumps(self.conversation, indent=4))
        print("========")
        reply = openai.ChatCompletion.create(model="gpt-4", messages = self.conversation)
        message = reply['choices'][0]['message']
        print(message)
        print()
        print("========")
        self.conversation.append(message)
        return message['content']

    def _store_state(self):
        with open(self.state_file, 'w') as f:
            json.dump({
                'conversation': self.conversation,
                'topic': self.topic,
                'avatars': self.avatars,
                'introductions': self.introductions,
                'next_message': self.next_message,
            }, f, indent=4)

    def _reload(self, i):
        with open(f'state{i}.json') as f:
            state = json.load(f)
        self.conversation = state['conversation']
        self.topic = state['topic']
        self.avatars = state['avatars']
        self.next_message = state['next_message']
        self.introductions = state.get('introductions',{})

    async def on_message(self, message):
        # Don't respond to messages from the bot itself
        if message.author == self.user:
            return

        if message.author.bot:
            print("Ignoring bot message.")
            return

        if message.type != discord.MessageType.default:
            return

        if str(message.channel.id) != channel_id:   # Only listen to the given channel
            return

        words = message.content.split(' ')
        author = message.author.name

        if len(words) == 0:
            return

        if words[0] == '!av':
            if len(words) >= 3:
                self.add_avatar(words[1], ' '.join(words[1:]))
            elif len(words) == 1:
                msg = 'Avatars:\n'
                for av in self.avatars:
                    intro = self.introductions.get(av, 'unknown')
                    msg += f'{av}: {intro}\n'
                await message.channel.send(msg)
            else:
                await message.channel.send(f'You need to give a description of {words[1]}')
        elif words[0] == '!topic':
            if len(words) >= 2:
                self.set_topic(' '.join(words[1:]))
            else:
                await message.channel.send(f'Current topic: {self.topic}')
        elif words[0] == '!reload':
            self._reload(int(words[1]))
            await message.channel.send('State reloaded')
        elif not words[0].startswith('!'):
            self.append_message(author, ' '.join(words[1:]))
            avatars = self.avatars
            async with message.channel.typing():
                reply = self.get_avatar_reply(avatars)
                await message.channel.send(reply)
        else:
            print(f'Unhandled: {words[0]}')
            return

        if not os.path.exists(self.state_file):
            await message.channel.send(f'(creating state file {self.state_i})')
        self._store_state()

# Instantiate your custom client class
client = MyBot()

# Run the bot using your token
client.run(token)
