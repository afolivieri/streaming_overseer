import json
import regex
import os
import asyncio
import signal
from telethon import TelegramClient, events
import logging
import traceback
import platform
import sys

# Configuration files
CREDENTIALS_FILE = 'credentials.json'
KEYWORDS_FILE = 'keywords.txt'
CHANNELS_FILE = 'channels.txt'


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)

async def get_credentials():
    try:
        if os.path.exists(CREDENTIALS_FILE):
            with open(CREDENTIALS_FILE, 'r') as file:
                credentials = json.load(file)
            if not credentials.get('channel_id'):
                credentials = await fetch_channel_id(credentials)
                with open(CREDENTIALS_FILE, 'w') as file:
                    json.dump(credentials, file, indent=4)
        else:
            credentials = {
                'api_id': input('Enter Telegram API ID: ').strip(),
                'api_hash': input('Enter Telegram API Hash: ').strip(),
                'phone': input('Enter phone number: ').strip(),
                'username': input('Enter username (optional, press enter to skip): ').strip() or None,
                'bot_token': input('Enter Telegram bot token: ').strip(),
                'channel_id': None
            }
            credentials = await fetch_channel_id(credentials)
            with open(CREDENTIALS_FILE, 'w') as file:
                json.dump(credentials, file, indent=4)
        return credentials
    except Exception as e:
        logging.error(f"Error in get_credentials: {e}")
        raise


async def fetch_channel_id(credentials):
    client = TelegramClient(credentials['username'] or 'anon_session',
                            credentials['api_id'], credentials['api_hash'])
    channel_name = input('Enter channel name: ')
    async with client:
        client.start(bot_token=credentials['bot_token'])
        async for dialog in client.iter_dialogs():
            if dialog.is_channel and dialog.name == channel_name:
                credentials['channel_id'] = dialog.id
                print(f"Found channel ID: {dialog.id}")
                break
    return credentials


def load_entries_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
        entries = [x.strip() for x in content.replace('\n', '').split(',') if x.strip()]
    return entries


def load_patterns():
    keywords = load_entries_from_file(KEYWORDS_FILE)
    word_patterns = {}
    emoji_pattern = r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]'

    for word in keywords:
        original_word = word
        if word.endswith('**'):
            word = word[:-2]
            pattern = rf'(?i)(?:{emoji_pattern})*{regex.escape(word)}\p{{L}}{{0,6}}'
        elif word.endswith('*'):
            word = word[:-1]
            pattern = rf'(?i)(?:{emoji_pattern})*{regex.escape(word)}\p{{L}}{{0,3}}'
        elif word.startswith('##'):
            word = word[2:]
            pattern = rf'(?i)(?:{emoji_pattern})*\d{{0,6}}{regex.escape(word)}'
        elif word.startswith('#'):
            word = word[1:]
            pattern = rf'(?i)(?:{emoji_pattern})*\d{{0,3}}{regex.escape(word)}'
        else:
            pattern = rf'(?i)(?:{emoji_pattern})*{regex.escape(word)}'
        try:
            compiled = regex.compile(pattern)
            word_patterns[original_word] = compiled
        except regex.error as e:
            logging.error(f'Invalid regex pattern for word "{word}": {e}')
    return word_patterns



async def shutdown(signal, client, loop):
    logging.info(f"Received exit signal {signal.name}...")
    await client.disconnect()
    loop.stop()


async def main():
    try:
        creds = await get_credentials()
        client = TelegramClient(creds['username'] or 'anon_session', creds['api_id'], creds['api_hash'])
        await client.start(phone=creds['phone'])

        word_patterns = load_patterns()
        channels = load_entries_from_file(CHANNELS_FILE)
        channel_id = creds['channel_id']  # Use the channel ID from credentials
        await client.send_message(channel_id, f"Listening to {', '.join(channels)}...")

        @client.on(events.NewMessage(chats=channels))
        async def handler(event):
            try:
                message_content = event.message.message if event.message else ""
                words = []
                contexts = []
                for word, pattern in word_patterns.items():
                    for match in pattern.finditer(message_content):
                        start_pos = max(match.start() - 20, 0)
                        end_pos = min(match.end() + 20, len(message_content))
                        context = message_content[start_pos:end_pos]
                        words.append(word)
                        contexts.append(context)
                await client.send_message(channel_id, f"Keyword Match: {', '.join(words)}\nContext: {', '.join(contexts)}")
                await asyncio.sleep(0.1)
                await event.message.forward_to(channel_id)
                await asyncio.sleep(0.5)
                print(f'Forwarded Message: {message_content}')
            except Exception as e:
                logging.error(f"Error in message handler: {e}")

        logging.info(f"Listening to {', '.join(channels)}...")

        loop = asyncio.get_event_loop()
        if platform.system() != 'Windows':
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(shutdown(s, client, loop)))
        else:
            try:
                await client.run_until_disconnected()
            except KeyboardInterrupt:
                await shutdown(signal.SIGINT, client, loop)
        await client.run_until_disconnected()
    except Exception as e:
        logging.error(f"Error in main: {e}")
        logging.error(traceback.format_exc())
    finally:
        logging.info("Disconnecting client...")
        await client.disconnect()
        logging.info("Client disconnected safely.")


if __name__ == '__main__':
    asyncio.run(main())
