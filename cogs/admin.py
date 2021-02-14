from discord.ext import commands
import discord
import datetime
from psutil import virtual_memory, cpu_percent, cpu_freq
from bot_errors import NoPermissionError, NotOnServerError
import pytz

start_time = datetime.datetime.utcnow()


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def check_mod(self, user):
        try:
            for userid in self.bot.config['owners']:
                if str(user.id) in str(userid):
                    return True
        except AttributeError:
            raise NotOnServerError

        return False

    @commands.command(name='say')
    async def say_text(self, ctx, *, _text):
        '''Sends whatever is put into the command'''
        if self.check_mod(ctx.message.author):
            try:
                await ctx.message.delete()
            except Exception:
                pass
        else:
            raise NoPermissionError

        await ctx.send(_text)

    @commands.command(name='clear', aliases=['cls', 'purge'])
    async def clear(self, context, limit: int):
        if context.message.author.guild_permissions.administrator:
            purged_messages = await context.message.channel.purge(limit=limit)
            embed = discord.Embed(
                title='Nothing to see here',
                description=f'**{context.message.author}** cleared **{len(purged_messages)}** messages!',
                color=0x00FF00
            )
            await context.send(embed=embed)
        else:
            embed = discord.Embed(
                title='Error!',
                description='You don\'t have the permission to use this command.',
                color=0x00FF00
            )
            await context.send(embed=embed)


def setup(bot):
    bot.add_cog(Admin(bot))
