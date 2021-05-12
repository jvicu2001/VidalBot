import discord
from discord.ext import commands
import asyncio
import aiohttp
from akinator.async_aki import Akinator

aki_lang = 'es'

question_emojis = (
    '✅',
    '❌',
    '❓',
    '📈',
    '📉',
    '↩️'
)

guess_emojis = ('✅','❌')


class Akinator_Game(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def question_embed(self, ctx, question_text, player, step):
        description = ''
        if step == 0:
            description = "{} = Sí\n \
            {} = No\n \
            {} = No sé\n \
            {} = Probablemente\n \
            {} = Probablemente no".format(
                                        question_emojis[0],
                                        question_emojis[1],
                                        question_emojis[2],
                                        question_emojis[3],
                                        question_emojis[4]
                                        )
        else:
            description = "{} = Sí\n \
            {} = No\n \
            {} = No sé\n \
            {} = Probablemente\n \
            {} = Probablemente no\n \
            {} = Retroceder una pregunta".format(
                                        question_emojis[0],
                                        question_emojis[1],
                                        question_emojis[2],
                                        question_emojis[3],
                                        question_emojis[4],
                                        question_emojis[5]
                                        )
        
        embed = discord.Embed(
            title=question_text,
            type='rich',
            color=0xC5F5F0,
            description=description
            )
        embed.set_footer(
            text="{}. Pregunta n°{}".format(player.display_name, step+1),
            icon_url=player.avatar_url
        )
        return embed
        
    async def guess_embed(self, ctx, guess, player):
        embed = discord.Embed(
            title=guess['name'],
            type='rich',
            color=0x00AD8B,
            description='{}\n¿Es este tu personaje?'.format(guess["description"])
            )
        embed.set_footer(
            text="{}".format(player.display_name),
            icon_url=player.avatar_url
        )
        embed.set_image(url=guess['absolute_picture_path'])
        
        return embed

    async def timeout_embed(self):
        return discord.Embed(
            title='¡Se te acabó el tiempo!',
            type='rich',
            color=0xFF2000,
            description='Pasaron 2 minutos sin que dieras una respuesta\n\
                Puedes iniciar una partida nueva si quieres volver a jugar'
            )
            
    async def question_limit_embed(self):
        return discord.Embed(
            title='¡Se acabaron las preguntas!',
            type='rich',
            color=0xFF2000,
            description='¡Me has vencido!'
            )

    async def win_embed(self, guess, player):
        embed = discord.Embed(
            title=guess['name'],
            type='rich',
            color=0xffd700,
            description='**¡Genial! He adivinado bien una vez más.**\n\
                Juguemos otra vez.'
            )
        embed.set_image(url=guess['absolute_picture_path'])

        embed.set_footer(
            text="{}".format(player.display_name),
            icon_url=player.avatar_url
        )
        return embed
    
    async def question_fill_react(self, msg, step):
        if step == 0:
            for emoji in question_emojis[:-1]:
                await msg.add_reaction(emoji)
                await asyncio.sleep(0.5)
        else:
            for emoji in question_emojis:
                await msg.add_reaction(emoji)
                await asyncio.sleep(0.5)

    async def guess_fill_react(self, msg):
        for emoji in guess_emojis:
            await msg.add_reaction(emoji)
            await asyncio.sleep(0.5)
    
    
    @commands.command(
        name='akinator',
        aliases=['aki'],
        help='Juega una partida de Akinator.\n \
            Se usan las reacciones puestas por el bot en la \
                pregunta para seleccionar tu respuesta.\n\
            Nota: Hay que esperar a que el bot termine de colocar las \
                reacciones para que funcione correctamente.',
        brief='Juega a Akinator!'
        )
    async def aki(self, ctx):
        player = ctx.author
        game = Akinator()
        question = await game.start_game(language=aki_lang)
        win = False
        game_embed = await self.question_embed(ctx, question, player, game.step)
        game_message = await ctx.send(embed=game_embed)
        await self.question_fill_react(game_message, game.step)
        
        # Check if the original user reacted with one of the correct emojis
        def question_react_check(reaction, user):
            return (user == player and str(reaction.emoji) in question_emojis)

        def guess_react_check(reaction, user):
            return (user == player and str(reaction.emoji) in guess_emojis)

        
        while (win is False and game.step < 80):
            
            # Wait for reaction answer from original user
            try:
                reaction, user = await self.bot.wait_for(
                    "reaction_add",
                    timeout=120.0,
                    check=question_react_check
                    )
            # If it times out, the game embed is replaced by a game over embed
            except asyncio.TimeoutError:
                await game_message.clear_reactions()
                game_embed = await self.timeout_embed()
                await game_message.edit(embed=game_embed)
                break
            
            # Sends the answer to akinator or rolls back one question
            else:
                answer = question_emojis.index(str(reaction.emoji))
                if answer in range(5):
                    question = await game.answer(answer)
                if answer == 5:
                    question = await game.back()
            
            # Ask if the current guess is correct
            if game.progression >= 80 or game.step == 80:
                guess = await game.win()
                await game_message.clear_reactions()
                game_embed = await self.guess_embed(ctx, guess, player)
                await game_message.edit(embed=game_embed)
                await self.guess_fill_react(game_message)
                
                try:
                    reaction, user = await self.bot.wait_for(
                        "reaction_add",
                        timeout=120.0,
                        check=guess_react_check
                        )
                
                except asyncio.TimeoutError:
                    await game_message.clear_reactions()
                    game_embed = await self.timeout_embed()
                    await game_message.edit(embed=game_embed)
                    break

                # Win if the answer is positive
                else:
                    answer = guess_emojis.index(str(reaction.emoji))
                    
                    # Win and end game loop
                    if answer == 0:
                        win = True
                        continue
            
            
            await game_message.clear_reactions()
            game_embed = await self.question_embed(ctx, question, player, game.step)
            await game_message.edit(embed=game_embed)
            await self.question_fill_react(game_message, game.step)

        if win:
            await game_message.clear_reactions()
            game_embed = await self.win_embed(game.first_guess, player)
            return await game_message.edit(embed=game_embed)
            
        else:
            await game_message.clear_reactions()
            game_embed = await self.question_limit_embed(game.first_guess)
            return await game_message.edit(embed=game_embed)

        
        
def setup(bot):
    bot.add_cog(Akinator_Game(bot))