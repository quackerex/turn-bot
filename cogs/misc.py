import discord
from discord.ext import commands


class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='ping', aliases=['latency'])
    async def ping(self, ctx):
        """ Pong! """
        message = await ctx.send(":ping_pong: Pong!")
        ping = (message.created_at.timestamp() -
                ctx.message.created_at.timestamp()) * 1000
        await message.edit(content=f":ping_pong: Pong!\nTook `{int(ping)}ms`\nLatency: `{int(self.bot.latency*1000)}ms`")

    @commands.command(name='owner', aliases=['support', 'contact'])
    async def support(self, ctx, *, msg: str = ""):
        """Contact bot owner"""
        if msg == "":
            return await ctx.send("Please enter a message to send towards Bot Owner", delete_after=5.0)

        embed = discord.Embed(colour=discord.Colour(0x5dadec), description=msg)
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
        embed.set_footer(
            text=f"{ctx.guild} : {ctx.guild.id}", icon_url=ctx.guild.icon_url)

        info = await self.bot.application_info()
        await info.owner.send(embed=embed)
        await ctx.send("Bot owner notified!")


def setup(bot):
    bot.add_cog(Misc(bot))
