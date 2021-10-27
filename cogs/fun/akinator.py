import asyncio

import discord
from discord.errors import Forbidden
from discord.ext import commands
from discord_components import Button, ButtonStyle, DiscordComponents

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

available_langs = (
    "en", # English (default)
    "en_animals", # English server for guessing animals
    "en_objects", # English server for guessing objects
    "ar", # Arabic
    "cn", # Chinese
    "de", # German
    "de_animals", # German server for guessing animals
    "es", # Spanish
    "es_animals", # Spanish server for guessing animals
    "fr", # French
    "fr_animals", # French server for guessing animals
    "fr_objects", # French server for guessing objects
    "il", # Hebrew
    "it", # Italian
    "it_animals", # Italian server for guessing animals
    "jp", # Japanese
    "jp_animals", # Japanese server for guessing animals
    "kr", # Korean
    "nl", # Dutch
    "pl", # Polish
    "pt", # Portuguese
    "ru", # Russian
    "tr", # Turkish
    "id", # Indonesian
)

guess_emojis = ('✅','❌')



class Akinator_Game(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.category = "Fun"
        DiscordComponents(bot)
    
    # Obtiene los botones correspondientes a la situación
    async def get_buttons(self, guess: bool, step: int, disabled: bool = False):
        buttons = [[
            Button(
                style=ButtonStyle.green,
                label='Sí',
                emoji=question_emojis[0],
                disabled=disabled
            ),
            Button(
                style=ButtonStyle.red,
                label='No',
                emoji=question_emojis[1],
                disabled=disabled
            )
        ]]

        if guess:
            return buttons

        buttons[0] += [
            Button(
                style=ButtonStyle.gray,
                label='No sé',
                emoji=question_emojis[2],
                disabled=disabled
            ),
            Button(
                style=ButtonStyle.blue,
                label='Probablemente',
                emoji=question_emojis[3],
                disabled=disabled
            ),
            Button(
                style=ButtonStyle.blue,
                label='Probablemente No',
                emoji=question_emojis[4],
                disabled=disabled
            )
        ]
        if step == 0:
            return buttons

        buttons.append(
            Button(
                style=ButtonStyle.gray,
                label='Volver',
                emoji=question_emojis[5],
                disabled=disabled
            )
        )
        return buttons

    # Embed de oregunta
    async def question_embed(self, ctx, question_text, player, step, color):
        embed = discord.Embed(
            title=question_text,
            type='rich',
            color=color
            )
        embed.set_footer(
            text="{}. Pregunta n°{}".format(player.display_name, step+1),
            icon_url=player.avatar_url
        )
        return embed
        
    # Embed del personaje que Akinator cree que buscas
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

    # Embed de TimeOut (Pasaron 2 minutos sin respuesta)
    async def timeout_embed(self):
        return discord.Embed(
            title='¡Se te acabó el tiempo!',
            type='rich',
            color=0xFF2000,
            description='Pasaron 2 minutos sin que dieras una respuesta\n\
                Puedes iniciar una partida nueva si quieres volver a jugar'
            )
            
    # Embed de cuando se acaban las preguntas
    async def question_limit_embed(self):
        return discord.Embed(
            title='¡Se acabaron las preguntas!',
            type='rich',
            color=0xFF2000,
            description='¡Me has vencido!'
            )

    # Embed cuando se gana el juego
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

    # Se obtiene el color del embed de pregunta según el porcentaje de progreso
    def progression_color(self, progression):
        return discord.Colour.from_hsv(progression*0.00333, 0.74, 1.0)

    
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.command(
        name='akinator',
        aliases=['aki'],
        help=f'Juega una partida de Akinator.\n \
            Se usan las reacciones puestas por el bot en la pregunta para seleccionar tu respuesta\n \
            Lenguajes disponibles: {str(available_langs)}',
        brief='Juega a Akinator!'
        )
    async def aki(self, ctx: commands.Context, lang: str = None):
        # Inicialización de variables y del objeto de la partida
        player = ctx.author
        game = Akinator()
        game_lang = aki_lang
        if lang in available_langs:
            game_lang = lang
        async with ctx.channel.typing():
            question = await game.start_game(language=game_lang)
            win = False
            color = self.progression_color(game.progression)
            game_embed = await self.question_embed(ctx, question, player, game.step, color)
            buttons = await self.get_buttons(False, 0)
            game_message = await ctx.send(embed=game_embed, components=buttons)
        rejected_guesses = set()
        
        # Checkeo del botón, revisa si el jugador y el mensaje son los correctos
        def button_check(res):
            return (res.user == player and res.message == game_message)

        
        while (win is False and game.step <= 79):
            
            # Espera 2 minutos a que el jugador presione el botón
            try:
                res = await self.bot.wait_for(
                    "button_click",
                    timeout=120.0,
                    check=button_check
                )
            # Si pasa ese tiempo sin acción del jugador, finaliza el juego por TimeOut
            except asyncio.TimeoutError:
                game_embed = await self.timeout_embed()
                try:
                    return await game_message.edit(embed=game_embed, components=None)
                except Forbidden:
                    return await ctx.send(embed=game_embed)
            
            # Si se recive una respuesta, esta se envía a Akinator
            # En caso de retroceder, se obtiene la pregunta anterior.
            else:
                buttons = await self.get_buttons(False, game.step, True)
                await game_message.edit(components=buttons)
                answer = question_emojis.index(str(res.component.emoji))
                if answer in range(5):
                    question = await game.answer(answer)
                if answer == 5:
                    question = await game.back()
            
            # Se pregunta si la sugerencia de Akinator es la correcta
            # cuando Akinator está seguro en un 80% o más de que está en
            # lo correcto o cuando queda la última pregunta.
            if game.progression >= 80 or game.step >= 79:
                guess = await game.win()
                
                # Se salta el preguntar por el personaje si ya se rechazó
                # una vez, a menos que sea la última pregunta.
                if guess['id'] not in rejected_guesses or game.step >= 79:
                    async with ctx.channel.typing():
                        game_embed = await self.guess_embed(ctx, guess, player)
                        buttons = await self.get_buttons(True, -1)
                        try:
                            await game_message.edit(embed=game_embed, components=buttons)
                        except Forbidden:
                            game_message = await ctx.send(embed=game_embed, components=buttons)
                    
                    try:
                        res = await self.bot.wait_for(
                            "button_click",
                            timeout=120.0,
                            check=button_check
                            )
                    
                    # Si se acaba el tiempo, se detiene el juego por TimeOut
                    except asyncio.TimeoutError:
                        game_embed = await self.timeout_embed()
                        try:
                            #await game_message.clear_reactions()
                            return await game_message.edit(embed=game_embed, components=None)
                        except Forbidden:
                            return await ctx.send(embed=game_embed)

                    # "Ganar" si la respuesta del jugador es positiva
                    else:
                        buttons = await self.get_buttons(True, game.step, True)
                        await game_message.edit(components=buttons)
                        answer = guess_emojis.index(str(res.component.emoji))
                        
                        # Dejar el bool de ganar en verdadero. Esto hace que se
                        # deje de cumplir la condición del loop del juego.
                        if answer == 0:
                            win = True
                            continue
                        
                        # Se añade la respuesta rechazada a un set a ignorar
                        # En caso de que sea la última pregunta, se sale del loop
                        # dejando el bool de ganar en falso.
                        else:
                            if game.step > 79:
                                break
                            rejected_guesses.add(guess['id'])
            
            # En caso de que no se esté intentando dar un personaje, mostrar el embed
            # de la siguiente pregunta
            async with ctx.channel.typing():
                color = self.progression_color(game.progression)
                game_embed = await self.question_embed(ctx, question, player, game.step, color)
                buttons = await self.get_buttons(False, game.step)
                try: 
                    await game_message.edit(embed=game_embed, components=buttons)
                except Forbidden:
                    game_message = await ctx.send(embed=game_embed, components=buttons)
                
        # Si se gana, se envía el embed de partida ganada.
        if win:
            game_embed = await self.win_embed(game.first_guess, player)
            try:
                return await game_message.edit(embed=game_embed, components=None)
            except Forbidden:
                return await ctx.send(embed=game_embed)

        # En caso contrario, donde se acaban las preguntas, se envía el embed
        # de que Akinator se quedó sin preguntas.
        else:
            game_embed = await self.question_limit_embed()
            try:
                return await game_message.edit(embed=game_embed, components=None)
            except Forbidden:
                return await ctx.send(embed=game_embed)

    @aki.error
    async def aki_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.errors.MaxConcurrencyReached):
            await ctx.send('¡Ya estás jugando!')
        else:
            await ctx.send(f'Ha ocurrido un error.\n```\n{error}\n```')

        
        
def setup(bot):
    bot.add_cog(Akinator_Game(bot))
