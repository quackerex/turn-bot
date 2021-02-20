from discord.ext import commands, tasks
import discord
import typing
import asyncio
import logging
import random
import json
import re
import datetime

from resources.DatabaseInterface import DatabaseInterface
from resources.DatabaseModels import Country
from random import randint
from bot_errors import CountryNotFound

log = logging.getLogger('bot')


class Game(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.interface = DatabaseInterface()
        self.index = 14
        # self.status_updater_task.start()

    def random_color(self):
        return discord.Color.from_rgb(random.randint(1, 255), random.randint(1, 255), random.randint(1, 255))

    def random_quote(self):
        with open('quotes.json') as fp:
            data = json.load(fp)
            random_index = randint(0, len(data)-1)
            return data[random_index]

    def message_link(self, guild_id, channel_id, message_id):
        return f'https://discordapp.com/channels/{guild_id}/{channel_id}/{message_id}'

    def stats_embed(self, country):
        emb = discord.Embed(colour=self.random_color(),
                            title=country.name)
        emb.add_field(name='Polpow', value=str(
            country.polpow), inline=True)
        emb.add_field(name='Stability', value=str(
            country.stability), inline=True)
        emb.add_field(name='War Support', value=str(
            country.war_support), inline=True)
        emb.add_field(name='Crime', value=str(
            country.crime), inline=True)
        emb.add_field(name='Population', value=str(
            country.population), inline=True)
        emb.add_field(name='Empire Sprawl', value=str(
            country.empire_sprawl), inline=True)
        emb.add_field(name='Legitimancy', value=str(
            country.legitimancy), inline=True)
        emb.set_footer(text=self.random_quote())

        return emb

    async def set_channel_perms(self, channel, sendMessage: bool):
        server = channel.guild
        overwrites_everyone = channel.overwrites_for(server.default_role)
        overwrites_everyone.send_messages = sendMessage
        await channel.set_permissions(server.default_role, overwrite=overwrites_everyone)

    async def set_status(self, status, text, *, force=False):
        game = discord.Game(text)

        # We only want to send a request if the status is different
        # or if the status is not set.
        # The below returns if either of those requirements are not met.
        now = datetime.datetime.utcnow()
        # if (
        #     not force
        #     # and self.last_set
        #     # and self.last_set + datetime.timedelta(minutes=30) < now
        #     and self.activity == game
        #     and self.status == status
        # ):
        #     return

        await self.bot.change_presence(status=status, activity=game)
        self.status = status
        self.activity = game

        log.info(f"Set status to {status}: {text}")

    @commands.command(pass_context=True)
    @commands.guild_only()
    async def countries(self, ctx):
        countries_list = self.interface.get_all(Country)
        countries = '\n'.join('' + c.name for c in countries_list)
        await ctx.send(countries)

    @commands.guild_only()
    @commands.command(pass_context=True)
    async def info(self, ctx, player: typing.Union[discord.Member, str] = None):
        # typing.Union[discord.Member, str]
        player_country = None

        if player == None:
            player = ctx.author

        if isinstance(player, discord.Member):
            try:
                player_country = self.interface.find_country_by_player(
                    player.id)
            except CountryNotFound:
                return await ctx.send('That player doesn\'t have a country')

        elif isinstance(player, str):
            try:
                player_country = self.interface.find_country_by_name(
                    str(player))
            except CountryNotFound:
                return await ctx.send('That country name does not exist')
        # else:
        #     return await ctx.send('Search Country by name is not supported yet')

        emb = self.stats_embed(player_country)

        await ctx.send(embed=emb)

    @commands.command(pass_context=True)
    @commands.guild_only()
    async def start(self, ctx):
        await self.bot.set_status(discord.Status.idle, 'Starting the game', force=False)
        self.round_task.start()
        return await ctx.message.add_reaction(emoji='✅')

    @commands.command(pass_context=True)
    @commands.guild_only()
    async def stop(self, ctx):
        await self.bot.set_status(discord.Status.idle, 'Game haven\'t started yet', force=False)
        self.round_task.cancel()
        countries = self.interface.get_all(Country)
        log.info('Starting cleanup')
        for c in countries:
            channel_id = c.channel_id
            channel = self.bot.get_channel(channel_id)
            server = channel.guild
            overwrites_everyone = channel.overwrites_for(server.default_role)
            overwrites_everyone.send_messages = False
            await channel.set_permissions(server.default_role, overwrite=overwrites_everyone)
            fetch_previous_msg = await channel.history().find(lambda m: m.author.id == self.bot.user.id and ('It\'s your turn' in m.content))
            if fetch_previous_msg:
                await fetch_previous_msg.delete()
                await fetch_previous_msg.channel.send('Waiting for your turn')
        return await ctx.message.add_reaction(emoji='✅')

    @commands.command(pass_context=True)
    @commands.guild_only()
    async def change_turn(self, ctx, number: int):
        if self.round_task.is_running():
            return ctx.send('Stop the round before using this command')
        countries = self.interface.get_all(Country)
        if len(countries) > number:
            self.index = number
            country = countries[self.index]
            c = self.interface.change_the_turn(country)
            # await ctx.send(last_country.name)
            await ctx.send(f'Changed the turn to {c.name}')
        else:
            await ctx.send(f'The number is too large')

    @commands.command(pass_context=True)
    @commands.guild_only()
    async def reset(self, ctx):
        if self.round_task.is_running():
            return await ctx.send('Stop the round before using this command')
        await self.bot.set_status(discord.Status.idle, 'Game haven\'t started yet', force=False)
        countries = self.interface.get_all(Country)
        category = self.bot.get_channel(794781781302706206)
        await category.edit(name='ROUND 1')

        for c in countries:
            channel_id = int(c.channel_id)
            channel = self.bot.get_channel(channel_id)
            # cOriginalName = channel.name
            await self.set_channel_perms(channel, False)
            # server = channel.guild
            # overwrites_everyone = channel.overwrites_for(server.default_role)

            # overwrites_everyone.send_messages = False
            # await channel.set_permissions(server.default_role, overwrite=overwrites_everyone)

        return await ctx.message.add_reaction(emoji='✅')

    @tasks.loop(seconds=1)
    async def round_task(self):

        countries = self.interface.get_all(Country)
        wait_msg = None
        log_channel = self.bot.get_channel(795610387126288394)

        category = self.bot.get_channel(794781781302706206)
        round_num = re.findall('\d+', category.name)[0]

        while self.index < len(countries):
            channel_id = int(countries[self.index].channel_id)

            log.info('Turn: ' + countries[self.index].name)
            self.interface.change_the_turn(countries[self.index])

            channel = self.bot.get_channel(channel_id)

            self.set_channel_perms(channel, True)

            # server = channel.guild
            # overwrites_everyone = channel.overwrites_for(server.default_role)
            # overwrites_everyone.send_messages = True
            # await channel.set_permissions(server.default_role, overwrite=overwrites_everyone)

            fetch_previous_msg = await channel.history().find(lambda m: m.author.id == self.bot.user.id and ('Waiting for your turn' in m.content or 'It\'s your turn' in m.content))
            if fetch_previous_msg:
                await fetch_previous_msg.delete()

            user = channel.guild.get_member(countries[self.index].president_id)
            emb = self.stats_embed(countries[self.index])
            turn_msg = await channel.send(f'||{user.mention}||\nIt\'s your turn', embed=emb)

            await self.bot.set_status(discord.Status.online, f'Current turn: {countries[self.index].name}', force=False)

            def check(m):
                owners = [442903946139271179, 316385640323481601,
                          468296341093613569, 325594915218128900]
                if m.channel == channel and not m.author.bot:
                    if m.author.id in owners:
                        return False
                    return True
                return False

            user_msg = await self.bot.wait_for('message', check=check, timeout=86400)

            emb = discord.Embed(colour=self.random_color(),
                                title=f'Round {round_num} - {countries[self.index].name}\'s Turn',
                                description=user_msg.content if user_msg.content else 'Timeout',
                                url=self.message_link(user_msg.guild.id, user_msg.channel.id, user_msg.id),)
            emb.set_footer(
                text=f'Send by  {user_msg.author.display_name} in #{user_msg.channel} ({user_msg.guild})', icon_url=user_msg.author.avatar_url)
            await log_channel.send(embed=emb)

            self.interface.change_the_turn(countries[self.index])

            # reset the permission
            self.set_channel_perms(channel, False)
            # overwrites_everyone.send_messages = False
            # await channel.set_permissions(server.default_role, overwrite=overwrites_everyone)

            await turn_msg.delete()
            wait_msg = await channel.send('Waiting for your turn')

            self.index += 1

        new_round_num = int(round_num) + 1
        category_name = 'ROUND {}'.format(new_round_num)
        await category.edit(name=category_name)
        await log_channel.send('Round {} Ended'.format(round_num))
        self.index = 0

    @round_task.before_loop
    async def before_round(self):
        # await self.bot.wait_until_ready()
        country = self.interface.get_last_turn()
        log.info('Starting from ' + country.name)
        self.index = country.id - 1 if country.id != 0 else 0


def setup(bot):
    bot.add_cog(Game(bot))
