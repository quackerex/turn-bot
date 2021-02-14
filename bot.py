# ive already did some coding
import discord
from discord.ext import commands

import yaml
import logging
import sys
import traceback
import os
import asyncio

import datetime

discord.VoiceClient.warn_nacl = False  # don't need this warning

formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] %(name)s: %(message)s', '%Y-%m-%d %H:%M:%S')
handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger = logging.getLogger('discord')
# logger.setLevel(logging.INFO)
logger.addHandler(handler)

log = logging.getLogger('bot')
log.setLevel(logging.INFO)

# create file handler which logs even debug messages
# fh = logging.FileHandler('log.log')
# fh.setLevel(logging.DEBUG)
# log.addHandler(fh)

logging.basicConfig(
    handlers=[logging.FileHandler('./logs/logfile.log', 'w', 'utf-8')],
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%m-%d %H:%M',
    level=logging.INFO  # CRITICAL ERROR WARNING  INFO    DEBUG    NOTSET
)

log.addHandler(handler)

initial_extensions = [
    'cogs.events',
    'cogs.game',
    'cogs.admin',
    'cogs.misc',
    'cogs.debug',
]


def get_prefix(bot, message):
    prefixes = [bot.config['prefix']]
    return commands.when_mentioned_or(*prefixes)(bot, message)


# send function/method for easy sending of embed messages with small amounts of text

description = '''IDK what to put here'''


class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents(messages=True, guilds=True, reactions=True)

        super().__init__(
            command_prefix=get_prefix,
            description=description,
            case_insensitive=False,
            activity=discord.Game('Starting up...'),
            help_command=commands.DefaultHelpCommand(),
            # intents=intents,
        )
        self.log = log

        log.info('Starting bot...')

        log.info('Loading config file...')
        self.config = self.load_config('config.yml')

        log.info('Loading extensions...')
        for extension in initial_extensions:
            self.load_extension(extension)

        log.info('Setting initial status before logging in...')

        self.init_ok = None
        self.restart_signal = None

        self.uptime = datetime.datetime.now()
        self.messages_in = self.messages_out = 0
        self.region = 'Melbourne, AU'

        try:
            self.load_extension('jishaku')

        except Exception:
            log.info('jishaku is not installed, continuing...')

    async def is_owner(self, user: discord.User):
        owners = [442903946139271179, 316385640323481601,
                  468296341093613569, 325594915218128900]
        for userid in owners:
            if user.id == userid:
                return True

        # Else fall back to the original
        return await super().is_owner(user)

    def load_config(self, filename):
        with open(filename, 'r') as f:
            return yaml.safe_load(f)

    async def set_status(self, status, text, *, force=False):
        game = discord.Game(text)

        # We only want to send a request if the status is different
        # or if the status is not set.
        # The below returns if either of those requirements are not met.
        now = datetime.datetime.utcnow()

        await self.change_presence(status=status, activity=game)
        self.status = status
        self.activity = game

        log.info(f"Set status to {status}: {text}")

    def run(self):
        log.info('Logging into Discord...')
        super().run(self.config['bot-token'])


if __name__ == '__main__':
    bot = Bot()
    bot.run()
