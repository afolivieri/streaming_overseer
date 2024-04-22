import json
import regex
import os
import asyncio
import signal
from telethon import TelegramClient, events

# Configuration files
CREDENTIALS_FILE = 'credentials.json'
KEYWORDS_FILE = 'keywords.txt'
CHANNELS_FILE = 'channels.txt'


async def get_credentials():
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


def load_patterns():
    with open(KEYWORDS_FILE, 'r', encoding='utf-8') as file:
        keywords = [x.strip() for x in file.read().split(',')]

    word_patterns = {}
    emoji_pattern = r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]'

    for word in keywords:
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
        word_patterns[word] = pattern
    return word_patterns


# Function to handle signals
def signal_handler(signal, frame):
    print('Detected Ctrl+C! Gracefully shutting down.')
    exit(0)


async def main():
    creds = await get_credentials()
    client = TelegramClient(creds['username'] or 'anon_session', creds['api_id'], creds['api_hash'])
    await client.start(phone=creds['phone'])

    word_patterns = load_patterns()
    channels = [x.strip() for x in open(CHANNELS_FILE, 'r').read().split(',')]
    channel_id = creds['channel_id']  # Use the channel ID from credentials
    await client.send_message(channel_id, f"Listening to {', '.join(channels)}...")

    @client.on(events.NewMessage(chats=channels))
    async def handler(event):
        message_content = event.message.message if event.message else ""
        for pattern in word_patterns.values():
            if regex.search(pattern, message_content):
                await event.message.forward_to(channel_id)
                print(f'Forwarded Message: {message_content}')
                break

    print(f"Listening to {', '.join(channels)}...")
    signal.signal(signal.SIGINT, signal_handler)
    try:
        await client.run_until_disconnected()
    finally:
        print("Disconnecting client...")
        await client.disconnect()
        print("Client disconnected safely.")


if __name__ == '__main__':
    asyncio.run(main())
