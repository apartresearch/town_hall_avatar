import json
import openai
import discord
import os
import random

API_ENDPOINT = 'https://discord.com/api/v10'
SYSTEM_MSG = "You are TownHallBot. Your role is to predict what different people will say on a given topic. Feel free to make the characters assertive and the conversations spicy!"

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
            {"role":"system","content":SYSTEM_MSG}
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
        if len(avatars) == 0:
            raise ValueError("No avatars")
        elif len(avatars) == 1:
            self.next_message += f'What would {avatars[0]} say on the topic?'
        else:
            avatar_list = ' and '.join(random.sample(avatars, k=len(avatars)))
            self.next_message += f'Out of {avatar_list} pick one or more people who would have an interesting and unique perspective on this. What would they say on the topic?'
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

    def _reload_empty(self):
        self.conversation = [
            {"role":"system","content":SYSTEM_MSG}
        ]
        self.topic = None
        self.avatars = []
        self.next_message = ''
        self.introductions = {}
        
    def _invent(self, keywords):
        if len(keywords) == 0:
            self.next_message += "Who would be a good person to add to the townhall? Invent a character that would offer a valuable, contrasting perspective from those already present. Give their name first and then a description, 3-5 sentences."
        else:
            keyword_string = ' '.join(keywords)
            self.next_message += f"""Invent a character based on the keywords "{keyword_string}". Give their name first and then a desccription, 3-5 sentences."""
        content = self._flush()
        print("\nInvention response:")
        print(content)
        print("==================\n")
        words = content.split(' ')
        for i in range(len(words)):
            if words[i][0] >= 'A' and words[i][0] <= 'Z':   # Find something that vaguely looks like a name?
                return words[i], ' '.join(words[i+1:])
        raise Exception(f"Unable to parse response: {content}")

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

        words = message.content.replace('"',"'").split(' ')
        author = message.author.display_name

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
        elif words[0] == '!invent':
            name, introduction = self._invent(words[1:])
            await message.channel.send(f'{name} {introduction}')
            self.add_avatar(name, introduction)
        elif words[0] == '!retire':
            if len(words) == 2:
                if words[1] in self.avatars:
                    self.avatars.remove(words[1])
                    await message.channel.send(f'{words[1]} has left the discussion.')
                else:
                    await message.channel.send(f'{words[1]} is not an avatar')
            else:
                await message.channel.send(f'Usage: retire <name>')
        elif words[0] == '!topic':
            if len(words) >= 2:
                self.set_topic(' '.join(words[1:]))
            else:
                await message.channel.send(f'Current topic: {self.topic}')
        elif words[0] == '!reload':
            if len(words) >= 2:
                self._reload(int(words[1]))
            else:
                self._reload_empty()
            await message.channel.send('State reloaded')
            return
        elif not words[0].startswith('!'):
            try:
                self.append_message(author, ' '.join(words[1:]))
                avatars = self.avatars
                for av in self.avatars:
                    if words[0] == av or words[0] == f'{av},' or words[0] == f'{av}:':
                        avatars = [av]
                        break

                if len(avatars) == 0:
                    await message.channel.send(f'No avatars')
                    return

                async with message.channel.typing():
                    reply = self.get_avatar_reply(avatars)
                    await message.channel.send(reply)
            except Exception as e:
                await message.channel.send(f'{type(e)}: {e}')
                return
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
