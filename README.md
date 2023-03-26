Create a secrets.json:

```json
{
    "bot_token": "",
    "discord_channel_id": "1089567159329505462",
    "oauth2_client_id": "",
    "oauth2_client_secret": "",
    "openai_key": ""
}
```

Run `get_oauth_url.py`. Send the URL to the server owner and get them to click through the flow to accept the bot into the server.

You'll need `discord` and `openai` packages installed and up to date.

Run `bot.py`
