### How to create and configure a Discord bot
https://medium.com/voice-tech-podcast/how-to-make-a-discord-bot-with-python-e066b03bfd9

### Installation
```shell
# install dependencies
# make sure numpy is installed
pip install pynacl google-cloud-speech grpc
apt-get install -y libopus-dev

# clone with the submodule
git clone --recursive https://github.com/vadimkantorov/discordspeechtotext
```

### Usage
```shell
# make sure to dump audio to debugdir instead of transcription, the discord client may be buggy, sometimes audio is cranky
python3 discord_speech_to_text_bot.py --discord-bot-token-file discordbottoken.txt --debug debugdir --text-channel-name general --voice-channel-name General

# run with google speech to text
python3 discord_speech_to_text_bot.py --discord-bot-token-file discordbottoken.txt --google-api-credentials-file googleapikeycredentials.json --text-channel-name general --voice-channel-name General

# you can also test your own speech-to-text system that serves a Google Cloud Speech2Text-like API; assumes your system listens at tcp://127.0.0.1:50000:
# example of third-party impl of Google Cloud Speech2Text API: https://github.com/vadimkantorov/convasr/blob/master/serve_google_api.py
python3 discord_speech_to_text_bot.py --discord-bot-token-file discordbottoken.txt --google-api-credentials-file= --endpoint 127.0.0.1:50000 --text-channel-name general --voice-channel-name General

# then in the text channel use commands:
#  "!transcribeyes" to start transcribing - the bot will send transcriptions of sound in the voice channel to the text channel
#  "!transcribenot" to stop transcribing
# one can specify --text-channel-id and --voice-channel-id for better control

```

### Background
Unfortunately, [discord.py](https://github.com/Rapptz/discord.py) does not support yet receiving voice (as opposed to [discord.js](https://github.com/discordjs/discord.js)). In the meanwhile I use @imayhaveborkedit's excellent [fork](https://github.com/imayhaveborkedit/discord.py). Hopefully, the changes will get merged upstream: https://github.com/Rapptz/discord.py/issues/1094, https://github.com/Rapptz/discord.py/issues/444
