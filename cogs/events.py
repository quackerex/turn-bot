import logging
from discord.ext import commands, tasks
import traceback
import discord
import asyncio
import sys
import random
import re
from discord.utils import get

from resources.DatabaseModels import Country
from resources.DatabaseInterface import DatabaseInterface
# from bot_errors import NoPermissionError

log = logging.getLogger('bot')



class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.interface = DatabaseInterface()

    @commands.Cog.listener()
    async def on_ready(self):
        log.info(f'Logged in as {self.bot.user.name} - {self.bot.user.id}')
        countries = self.interface.get_all(Country)
        log.info('Starting cleanup')
        for c in countries:
            channel_id = c.channel_id
            log.info('Done {}'.format(channel_id))
            channel = self.bot.get_channel(channel_id)
            server = channel.guild
            overwrites_everyone = channel.overwrites_for(server.default_role)
            overwrites_everyone.send_messages = False
            await channel.set_permissions(server.default_role, overwrite=overwrites_everyone)
            fetch_previous_msg = await channel.history().find(lambda m: m.author.id == self.bot.user.id and ('It\'s your turn' in m.content))
            if fetch_previous_msg:
                await fetch_previous_msg.delete()
                await fetch_previous_msg.channel.send('Waiting for your turn')
        
        await self.bot.set_status(discord.Status.idle, 'Game haven\'t started yet', force=False)
        
        log.info('Cleanup finished')

    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.author.bot:
            return
        if 'good' in msg.content.lower() and 'bot' in msg.content.lower():
            destination = None

            if msg.guild is None:
                destination = 'Private Message'
            else:
                destination = f'#{msg.channel} ({msg.guild})'

            log.info(f'{msg.author} in {destination}: {msg.content}')
            await msg.channel.send(random.choice(['😊', '😎', '{} is the best 😁'.format(msg.author.name)]))

        if 'bad bot' in msg.content.lower():
            destination = None

            if msg.guild is None:
                destination = 'Private Message'
            else:
                destination = f'#{msg.channel} ({msg.guild})'

            log.info(f'{msg.author} in {destination}: {msg.content}')
            await msg.channel.send('😥')

    @commands.Cog.listener()
    async def on_command(self, ctx):
        destination = None

        if ctx.guild is None:
            destination = 'Private Message'
        else:
            destination = f'#{ctx.channel} ({ctx.guild})'

        log.info(f'{ctx.author} in {destination}: {ctx.message.content}')

    @commands.Cog.listener()
    async def send_unexpected_error(self, ctx, error):
        if hasattr(error, 'original'):
            return
        em = discord.Embed(
            title=':warning: Unexpected Error',
            color=discord.Color.gold(),
        )

        description = (
            'An unexpected error has occured'
            f'```py\n{error}```\n'
        )

        em.description = description
        await ctx.send(embed=em)

    async def send_unexpected_error(self, ctx, error):
        em = discord.Embed(
            title=':warning: Unexpected Error',
            color=discord.Color.gold(),
        )

        description = (
            'An unexpected error has occured:'
            f'```py\n{error}```\n'
        )

        em.description = description
        await ctx.send(embed=em)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        red_tick = '\N{CROSS MARK}'

        if hasattr(ctx, 'handled'):
            return

        if isinstance(error, commands.NoPrivateMessage):
            message = await ctx.send(
                f'{red_tick} This command can\'t be used in DMs.'
            )

        # if hasattr(error, 'original'):
        #     if isinstance(error.original, NoPermissionError):
        #         message = await ctx.send('You don\'t have permission for that cool command.')

        elif isinstance(error, commands.ArgumentParsingError):
            message = await ctx.send(f'{red_tick} {error}')

        elif isinstance(error, commands.CommandOnCooldown):
            message = await ctx.send(
                f'{red_tick} You are on cooldown. Try again in {int(error.retry_after)} seconds.'
            )

        elif isinstance(error, commands.errors.BotMissingPermissions):
            perms = ''

            for perm in error.missing_perms:
                formatted = (
                    str(perm).replace('_', ' ').replace(
                        'guild', 'server').capitalize()
                )
                perms += f'\n- `{formatted}`'

            message = await ctx.send(
                f'{red_tick} I am missing some required permission(s):{perms}'
            )

        elif isinstance(error, commands.errors.BadArgument):
            message = await ctx.send(f'{red_tick} {error}')

        elif isinstance(error, commands.errors.MissingRequiredArgument):
            message = await ctx.send(
                f'{red_tick} Missing a required argument: `{error.param.name}`'
            )

        elif (
            isinstance(error, commands.CommandInvokeError)
            and str(ctx.command) == 'help'
        ):
            pass

        elif isinstance(error, commands.CommandInvokeError):
            original = error.original
            # if True: # for debugging
            if not isinstance(original, discord.HTTPException):
                log.exception(error)
                print(
                    'Ignoring exception in command {}:'.format(ctx.command),
                    file=sys.stderr,
                )
                traceback.print_exception(
                    type(error), error, error.__traceback__, file=sys.stderr
                )

                await self.send_unexpected_error(ctx, error)
                return


def setup(bot):
    bot.add_cog(Events(bot))
