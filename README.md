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
python3 discord_bot.py --discord-bot-token-file discordbottoken.txt --google-api-credentials-file googleapikeycredentials.json --text-channel-name general --voice-channel-name General

# then in the text channel use commands:
#  "!transcribeyes" to start transcribing - the bot will send transcriptions of sound in the voice channel to the text channel
#  "!transcribenot" to stop transcribing
# one can specify --text-channel-id and --voice-channel-id for better control
```

### Background
Unfortunately, [discord.py](https://github.com/imayhaveborkedit/discord.py) does not support yet receiving voice (as opposed to [discord.js](https://github.com/discordjs/discord.js). In the meanwhile I use @imayhaveborkedit's [fork](https://github.com/imayhaveborkedit/discord.py). Hopefully, the changes will get merged upstream: https://github.com/Rapptz/discord.py/issues/1094, https://github.com/Rapptz/discord.py/issues/444
