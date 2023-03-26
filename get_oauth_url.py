import json

with open('secrets.json') as f:
    secrets = json.load(f)

client_id = secrets['oauth2_client_id']
permissions = 67584
url = f'https://discord.com/oauth2/authorize?client_id={client_id}&scope=bot&permissions={permissions}'

print(url)
print('Send this to the server owner and they can add the bot to their server.')
