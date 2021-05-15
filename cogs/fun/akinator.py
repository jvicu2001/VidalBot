from operator import ge
import discord
from discord.colour import Colour
from discord.ext import commands
import asyncio
import aiohttp
from akinator.async_aki import Akinator
from enum import Enum

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

class AkinatorStatus(Enum):
    QUESTION = 0
    GUESS = 1
    TIMEOUT = 2
    WIN = 3
    LOSS = 4


class Akinator_Game(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def question_embed(self, ctx, question_text, player, step, color):
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
            color=color,
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
    
    async def question_fill_react(self, msg: discord.Message, player, reaction, step):
        # Remove player answer
        if reaction:
            await reaction.remove(player)
        cached_msg = discord.utils.get(self.bot.cached_messages, id=msg.id)
        if len(cached_msg.reactions) < 6:
            msg_emojis = map(lambda x : x.emoji, cached_msg.reactions)
            missing_reacts = list(filter(lambda x : x not in msg_emojis, question_emojis))
            if step == 0:
                if question_emojis[-1] in missing_reacts:
                    missing_reacts.remove(question_emojis[-1])
                if question_emojis[-1] in msg_emojis:
                    await msg.clear_reaction(question_emojis[-1])

            for emoji in missing_reacts:
                await msg.add_reaction(emoji)

    async def guess_fill_react(self, msg):
        #cached_msg = discord.utils.get(self.bot.cached_messages, id=msg.id)
        for emoji in guess_emojis:
            await msg.add_reaction(emoji)
            await asyncio.sleep(0.5)

    def progression_color(self, progression):
        return discord.Colour.from_hsv(progression*0.00333, 0.74, 1.0)

    
    
    @commands.command(
        name='akinator',
        aliases=['aki'],
        help='Juega una partida de Akinator.\n \
            Se usan las reacciones puestas por el bot en la \
                pregunta para seleccionar tu respuesta',
        brief='Juega a Akinator!'
        )
    async def aki(self, ctx):
        player = ctx.author
        game = Akinator()
        question = await game.start_game(language=aki_lang)
        win = False
        color = self.progression_color(game.progression)
        game_embed = await self.question_embed(ctx, question, player, game.step, color)
        game_message = await ctx.send(embed=game_embed)
        await self.question_fill_react(game_message, player, None, game.step)
        status = AkinatorStatus.QUESTION
        rejected_guesses = set()
        
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
                
                # Skip character guess if it was already rejected
                if guess['id'] not in rejected_guesses:
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
                        
                        # Add guess to rejected set
                        else:
                            rejected_guesses.add(guess['id'])
            
            
            # await game_message.clear_reactions()
            color = self.progression_color(game.progression)
            game_embed = await self.question_embed(ctx, question, player, game.step, color)
            await game_message.edit(embed=game_embed)
            await self.question_fill_react(game_message, player, reaction, game.step)

        if win:
            await game_message.clear_reactions()
            game_embed = await self.win_embed(game.first_guess, player)
            return await game_message.edit(embed=game_embed)
            
        else:
            await game_message.clear_reactions()
            game_embed = await self.question_limit_embed()
            return await game_message.edit(embed=game_embed)

        
        
def setup(bot):
    bot.add_cog(Akinator_Game(bot))