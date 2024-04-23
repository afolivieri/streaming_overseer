# Streaming Overseer: A Telegram Monitoring Tool

This tool monitors specified Telegram channels for messages that contain certain keywords and forwards them to a private channel. It's built using Python and Telethon, a Telegram client library.

## Features

- Monitors multiple channels.
- Searches for messages with specified keywords.
- Forwards matching messages to a private channel.

## Prerequisites

Before you can use this tool, you need to set up a few things:

1. **Python 3.8+** (Tested on 3.10+)
2. **Telethon Library**
3. **A Telegram API key and API Hash**
4. **A Telegram Bot**
5. **A Private Telegram Channel**

### Installing Python

Download and install Python from [python.org](https://www.python.org/downloads/).

## Setup Instructions

### Obtaining Telegram API ID and Hash

1. **Login to your Telegram account** at [Telegram Core](https://my.telegram.org).
2. Go to `API development tools` and fill out the form.
3. You will get an `api_id` and `api_hash` which are needed for the tool.

### Creating a Telegram Bot

1. **Open Telegram** and search for [BotFather](https://t.me/botfather).
2. Send `/newbot` and follow the instructions to create your bot.
3. **Copy the token** provided by BotFather.

### Setting Up a Private Channel

1. **Create a new channel** in Telegram.
2. **Switch the channel's privacy to private** in the channel settings.
3. **Add your bot as an administrator** to the channel.

## Configuration Files

The script uses several files for configuration:

- `credentials.json`: Automatically created if not present. It stores API keys, bot token, and private channel ID.
- `keywords.txt`: Contains keywords to monitor. Supports special modifiers for dynamic matching:
  - `*` at the end allows up to three additional characters.
  - `**` allows up to six additional characters.
  - `#` at the start includes numeric characters (up to three).
  - `##` includes numeric characters (up to six).

  **Note: Separate keywords using commas. Keywords can span multiple lines for readability; newlines are ignored.**
- `channels.txt`: List of channel usernames (the part after `t.me/`) to monitor
- Separate channel names with commas, and feel free to list them across multiple lines for better readability. Newlines between names are ignored.

  **Note: Ensure you have joined any channel you wish to monitor.**

### Examples

- `keywords.txt`
  ```
  hello*, world**, #123,
  ##123456, #or_any_combination**
  ```
- `channels.txt`
  ```
  python, daily_news,
  target3, target4
  ```


## Running the Tool

Execute the script:

```bash
python streaming_overseer.py
```

## Operational Details

- If not yet saved, the script will ask for your API ID, API hash, phone number, username, and bot token. 
- The script listens for new messages in the specified channels (You need to have joined the channels you intend to monitor).
- If a message contains any of the specified keywords, it is forwarded to the private channel.
- The script sends a startup message to the private channel when it begins monitoring.
- Use Ctrl+C to safely shut down the monitoring tool.