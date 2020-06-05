# needed until the fork is merged upstream
import sys; sys.path.insert(0, 'discord.py')

import argparse
import os
import time
import random
import asyncio
import numpy as np
import discord
import grpc
import google.oauth2.service_account
import google.cloud.speech_v1
import google.cloud.speech_v1.gapic.transports.speech_grpc_transport

class GoogleSpeechToText:
	def __init__(self, endpoint, lang, recognition_model, api_credentials = None):
		credentials = google.oauth2.service_account.Credentials.from_service_account_file(api_credentials) if api_credentials else grpc.local_channel_credentials()
		LocalSpeechGrpcTransport = type('LocalSpeechGrpcTransport', (google.cloud.speech_v1.gapic.transports.speech_grpc_transport.SpeechGrpcTransport, ), dict(create_channel = lambda self, address, credentials, **kwargs: grpc.secure_channel(address, credentials, **kwargs)))
		client_options = dict(api_endpoint = endpoint)

		self.client = google.cloud.speech_v1.SpeechClient(credentials = credentials, client_options = client_options) if api_credentials else google.cloud.speech_v1.SpeechClient(transport = LocalSpeechGrpcTransport(address = endpoint, credentials = credentials), client_options = client_options)
		self.lang = lang
		self.recognition_model = recognition_model

	def transcribe(self, pcm_s16le, sample_rate, num_channels):
		res = self.client.recognize(dict(audio_channel_count = num_channels, encoding = 'LINEAR16', sample_rate_hertz = sample_rate, language_code = self.lang, model = self.recognition_model), dict(content = pcm_s16le))
		hyp = res.results[0].alternatives[0].transcript if len(res.results) > 0 else ''
		return hyp

class DebugDumpRawAudio:
	def __init__(self, debug_dir):
		os.makedirs(debug_dir, exist_ok = True)
		self.debug_dir = debug_dir

	def transcribe(self, pcm_s16le, sample_rate, num_channels):
		audio_path = os.path.join(self.debug_dir, f'{int(time.time()).{random.randint(1000, 9999)}._s16le_hz{sample_rate}_ch{num_channels}.raw')
		with open(audio_path, 'wb') as f:
			f.write(pcm_s16le)
		print('ffplay -f s16le -ar {sample_rate} -ac {num_channels} "{audio_path}"')

class BufferAudioSink(discord.AudioSink):
	def __init__(self, flush):
		self.flush = flush
		self.NUM_CHANNELS = discord.opus.Decoder.CHANNELS
		self.NUM_SAMPLES = discord.opus.Decoder.SAMPLES_PER_FRAME
		self.SAMPLE_RATE_HZ = discord.opus.Decoder.SAMPLING_RATE
		self.BUFFER_FRAME_COUNT = 200
		self.buffer = np.zeros(shape = (self.NUM_SAMPLES * self.BUFFER_FRAME_COUNT, self.NUM_CHANNELS), dtype = 'int16')
		self.buffer_pointer = 0
		self.speaker = None

	def write(self, voice_data):
		if voice_data.user is None:
			return
		speaker = voice_data.user.id
		frame = np.ndarray(shape = (self.NUM_SAMPLES, self.NUM_CHANNELS), dtype = self.buffer.dtype, buffer = voice_data.data)
		speaking = np.abs(frame).sum() > 0
		need_flush = (self.buffer_pointer >= self.BUFFER_FRAME_COUNT - 2) or (not speaking and self.buffer_pointer > 0.5 * self.BUFFER_FRAME_COUNT) #or (self.speaker is not None and speaker != self.speaker)

		self.buffer[(self.buffer_pointer * self.NUM_SAMPLES) : ((1 + self.buffer_pointer) * self.NUM_SAMPLES)] = frame
		self.buffer_pointer += 1
		self.speaker = speaker

		if need_flush:
			print(self.buffer_pointer, speaking)

			pcm_s16le = self.buffer.tobytes()
			self.buffer.fill(0)
			self.buffer_pointer = 0
			self.flush(self.speaker, pcm_s16le, self.SAMPLE_RATE_HZ, self.NUM_CHANNELS)
				
class DiscordBotClient(discord.Client):
	def __init__(self, transcriber, text_channel_id = None, voice_channel_id = None, text_channel_name = None, voice_channel_name = None, *args, **kwargs):
		super().__init__(*args, **kwargs)
		discord.opus._load_default()
		
		self.transcriber = transcriber
		self.voice_client = None
		self.text_channel = None
		self.voice_channel = None
		self.speakingUserString = ''
		self.text_channel_id = text_channel_id
		self.text_channel_name = text_channel_name
		self.voice_channel_id = voice_channel_id
		self.voice_channel_name = voice_channel_name
		self.audioSink = BufferAudioSink(self.transcribe)
		self.messages = []
		self.loop.create_task(self.message_sending_loop())

	def transcribe(self, speaker, pcm_s16le, sample_rate, num_channels):
		hyp = self.transcriber.transcribe(pcm_s16le, sample_rate, num_channels)
		print('Transcribing', '[', hyp, ']')
		if hyp:
			self.messages.append((speaker, hyp)) 

	async def message_sending_loop(self, timeout = 0.25):
		while True:
			if not self.guilds or not self.messages:
				await asyncio.sleep(timeout)
				continue
				
			for speaker, hyp in self.messages:
				member = self.guilds[0].get_member(speaker)
				speaker_pretty = str(member.nick if member.nick is not None else member) if member is not None else 'N/A'
				await self.text_channel.send(f'[{speaker_pretty}] says: [{hyp}]')
			
			self.messages = []

	async def on_ready(self):
		print('\n'.join(map(repr, self.get_all_channels())))

		self.text_channel = discord.utils.get(self.get_all_channels(), **(dict(id = self.text_channel_id) if self.text_channel_id is not None else dict(name = self.text_channel_name)))
		self.voice_channel = discord.utils.get(self.get_all_channels(), **(dict(id = self.voice_channel_id) if self.voice_channel_id is not None else dict(name = self.voice_channel_name)))
			
		print('Logged in to Discord as {} - ID {}'.format(self.user.name, self.user.id))
		print('Ready to recieve commands!')

	async def on_message(self, message, timeout = 1.0):
		if message.author == self.user:
			return
		messageText = message.content.lower().strip()

		if messageText == '!transcribeyes':
			if self.voice_channel is not None:
				self.voice_client = await self.voice_channel.connect()
				self.voice_client.listen(self.audioSink)
				print("Connected!")

		elif messageText == '!transcribenot':
			if self.voice_client is not None:
				print("Attempting to hang up from voice channel")
				try:
					self.voice_client.stop()
					self.voice_client.stop_listening()
				except Exception as e:
					print(e)
				time.sleep(timeout)
				await self.voice_client.disconnect()
				self.voice_client = None
				print("Disconnected!")

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('--discord-bot-token-file', required = True)
	parser.add_argument('--google-api-credentials-file', required = True)
	parser.add_arugment('--debug', help = 'debug dir')
	parser.add_argument('--lang', default = 'ru-RU', help = 'see http://g.co/cloud/speech/docs/languages for a list of supported languages')
	parser.add_argument('--recognition-model', default = 'phone_call', choices = ['phone_call', 'default', 'video', 'command_and_search'])
	parser.add_argument('--endpoint', default = google.cloud.speech_v1.SpeechClient.SERVICE_ADDRESS)
	parser.add_argument('--text-channel-name', default = 'general')
	parser.add_argument('--voice-channel-name', default = 'General')
	parser.add_argument('--text-channel-id', type = int)
	parser.add_argument('--voice-channel-id', type = int)
	args = parser.parse_args()

	discord_bot_token = open(args.discord_bot_token_file).read().strip()

	transcriber = GoogleSpeechToText(endpoint = args.endpoint, recognition_model = args.recognition_model, lang = args.lang, api_credentials = args.google_api_credentials_file) if not args.debug else DebugDumpRawAudio(args.debug)
	bot = DiscordBotClient(text_channel_id = args.text_channel_id, voice_channel_id = args.voice_channel_id, text_channel_name = args.text_channel_name, voice_channel_name = args.voice_channel_name, transcriber = transcriber)
	bot.run(discord_bot_token)
