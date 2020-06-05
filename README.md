### How to create and configure a Discord bot
https://medium.com/voice-tech-podcast/how-to-make-a-discord-bot-with-python-e066b03bfd9

### Installation
```shell
# install dependencies
pip install pynacl
apt-get install -y libopus-dev

# install bot
git clone --recursive https://github.com/vadimkantorov/discordspeechtotext

# usage
python3 discord_bot.py --discord-bot-token-file discordbottoken.txt --google-api-credentials-file googleapikeycredentials.json
```

### Credits
Uses discord.py fork as a submodule: https://github.com/imayhaveborkedit/discord.py
