from telethon.sync import TelegramClient
from telethon.tl.types import ChannelParticipantsSearch
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.functions.messages import GetHistoryRequest
import argparse
import configparser
import logging

args_parser = argparse.ArgumentParser(description='Telegram parser')
args_parser.add_argument(
    '-c',
    '--config',
    type=str,
    default='telegramparser.conf',
    dest='config',
    help='config file path'
)
args_parser.add_argument(
    '-l',
    '--log',
    type=str,
    default='telegramparser.log',
    dest='log',
    help='log file path'
)
args = args_parser.parse_args()

config = configparser.ConfigParser()
config.read(args.config)

API_ID = int(config['telethon']['API_ID'])
API_HASH = config['telethon']['API_HASH']
SESSION_NAME = config['telethon']['SESSION_NAME']
PHONE = config['telethon']['PHONE']

logging.basicConfig(filename=args.log, level=logging.INFO)

client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
client.connect()
if not client.is_user_authorized():
    client.send_code_request(PHONE)
    client.sign_in(PHONE, input('Enter code: '))


async def parse_channel_info(channel) -> list:
    raw_channel_info = await client(GetFullChannelRequest(channel))

    channel_info = [{
        "title": raw_channel_info.chats[0].title,
        "participants_count": raw_channel_info.full_chat.participants_count
    }]

    logging.info('Parse channel info')

    return channel_info


async def parse_all_participants(channel) -> list:
    all_participants = []
    all_users_details = []
    filter_user = ChannelParticipantsSearch('')
    offset_user = 0
    limit_user = 100

    while True:
        participants = await client(GetParticipantsRequest(
            channel=channel,
            filter=filter_user,
            offset=offset_user,
            limit=limit_user,
            hash=0
        ))

        if not participants.users:
            break

        all_participants.extend(participants.users)
        offset_user += len(participants.users)

    for participant in all_participants:
        all_users_details.append({
            "prts": participant,
            "id": participant.id,
            "user": participant.username,
            "is_bot": participant.bot
        })

    logging.info('Parse channel participants info')

    return all_users_details


async def parse_all_messages(channel) -> list:
    all_messages = []

    while True:
        history = await client(GetHistoryRequest(
            peer=channel,
            offset_id=0,
            offset_date=None,
            add_offset=0,
            limit=100,
            max_id=0,
            min_id=0,
            hash=0
        ))

        if not history.messages:
            break

        messages = history.messages
        for message in messages:
            all_messages.append(message.to_dict())

        return all_messages


async def main():
    url = input('Enter URL of group or channel: ')
    channel = await client.get_entity(url)
    await parse_channel_info(channel)
    await parse_all_participants(channel)
    await parse_all_messages(channel)


with client:
    client.loop.run_until_complete(main())
