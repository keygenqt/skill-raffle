"""
Copyright 2021-2024 Vitaliy Zarubin

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import asyncio
import random
import sys
import time
from pathlib import Path

import click
from telethon import TelegramClient
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.functions.contacts import ResolveUsernameRequest
from telethon.tl.types import User

APP_NAME = 'raffle'
APP_VERSION = '0.0.1'


# Get telegram client
def get_client(api_id: int, api_hash: str) -> TelegramClient | None:
    async def _get_client() -> TelegramClient | None:
        try:
            client = TelegramClient(str(Path.home() / '.raffle_telegram.session'), api_id, api_hash)
            await client.connect()
            return client
        except (Exception,):
            pass
        return None

    # Run asynchronous method with return
    return run_blocking(_get_client)


# Run asynchronous method with return
def run_blocking(function):
    loop = asyncio.get_event_loop()
    task = loop.create_task(function())
    loop.run_until_complete(task)
    return task.result()


# Get list user channel
def get_users_channel(client: TelegramClient, channel_name: str, search: str | None) -> [User]:
    # asynchronous method
    async def _get_users_channel() -> [User]:
        users = []
        # Get users
        async with client:
            channel = await client(ResolveUsernameRequest(channel_name))
            if search:
                user_list = client.iter_participants(entity=channel, limit=200, search=search)
            else:
                user_list = client.iter_participants(entity=channel, limit=200)
            async for item in user_list:
                users.append(item)
        # Return list users
        return users

    # Run asynchronous method with return
    return run_blocking(_get_users_channel)


# Get count user channel
def get_users_count(client: TelegramClient, channel_name: str) -> int:
    # asynchronous method
    async def _get_users_count() -> int:
        # Get users
        async with client:
            channel_connect = await client.get_entity(channel_name)
            channel_full_info = await client(GetFullChannelRequest(channel=channel_connect))
            return channel_full_info.full_chat.participants_count

    # Run asynchronous method with return
    return run_blocking(_get_users_count)


# Get users with merge
def get_users(client: TelegramClient, channel_name: str, search: str | None, users: [User]) -> [User]:
    seconds = random.randint(1, 5)
    time.sleep(seconds)
    objects = get_users_channel(client, channel_name, search)
    ids = [item.id for item in users]
    for obj in objects:
        if obj.id not in ids:
            users.append(obj)
    return users


@click.group(invoke_without_command=True)
@click.version_option(version=APP_VERSION, prog_name=APP_NAME)
@click.option('--api_id', default=None, help='Telegram application ID', type=click.INT, required=True)
@click.option('--api_hash', default=None, help='Telegram application HASH', type=click.STRING, required=True)
@click.option('--channel', default=None, help='Telegram channel name', type=click.STRING, required=True)
@click.option('--user_search', default=None, help='Specify search user by name', type=click.STRING, required=False)
@click.option('--user_count', type=click.INT, default=3, help='Specify count user', required=False)
def main(api_id: int, api_hash: str, channel: str, user_search: str, user_count: int):
    """Find random users who will receive a prize."""

    # Get telegram client
    client = get_client(api_id=api_id, api_hash=api_hash)

    if not client:
        click.echo(click.style('Connect to telegram error', fg='red'))
        exit(1)

    # Get count users
    users_count = get_users_count(client, channel)

    click.echo('Start search...')

    # Get channel users
    users = get_users(client, channel, user_search, [])

    # Get random users
    random_users = random.sample(users, user_count)

    # Out about find count
    click.echo('{} {}'.format(click.style('Total users:', fg='blue'), users_count))
    click.echo('{} {}'.format(click.style('Search users:', fg='blue'), len(users)))

    click.echo(click.style('Congratulations to the following subscribers!', fg='green'))

    # Out random users
    for index, user in enumerate(random_users):
        click.echo(('{index}. {fname} {lname}'.format(
            index=click.style(index + 1, fg='blue'),
            fname=user.first_name,
            lname=user.last_name
        ) + '\t' + '(id: {}, username: {})'.format(
            user.id,
            user.username,
        )).expandtabs(30))


if __name__ == '__main__':
    if len(sys.argv) == 1:
        main.main(['--help'])
    else:
        main()
