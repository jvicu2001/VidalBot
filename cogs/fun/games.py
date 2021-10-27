from random import randint
import re

import discord
from discord.ext import commands
import asyncio

class Sweeper(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.category = "Fun"

    states = {
        'BLANK': '🟦',
        'BOMB': '||💣||',
        1: '||1️⃣||',
        2: '||2️⃣||',
        3: '||3️⃣||',
        4: '||4️⃣||',
        5: '||5️⃣||',
        6: '||6️⃣||',
        7: '||7️⃣||',
        8: '||8️⃣||'
    }

    async def count_neighborgs(self, board, size: int, cell_x: int, cell_y: int) -> int:
        count: int = 0
        for _x in range(max(0, cell_x - 1), min(size, cell_x + 2)):
            for _y in range(max(0, cell_y - 1), min(size, cell_y + 2)):
                if (cell_x, cell_y) != (_x, _y):
                    if board[_x][_y] == self.states['BOMB']:
                        count += 1

        return count

    @commands.command(
        name='sweeper',
        aliases=['minesweeper', 'buscaminas', 'minas'],
        help='Juega al BuscaMinas\n\
            Ve revelando las celdas evitando encontrar una bomba.\n\
            El número de la celda indica cuántas bombas hay en celdas vecinas.\n\n\
            Puedes especificar el tamaño del área y la cantidad de minas.\n\
            Máximo tamaño: 10x10',
        brief='¡Juega a BuscaMinas!'
    )
    async def fill_board(self, ctx: commands.Context, size: int = 8, bombs: int = -1):
        async with ctx.channel.typing():
            # Limit board size. The theorical max should be 18x18 but for some reason
            # the message stops at around ~115 cells. Maybe there0s a limit on how many
            # spoilers a message can have. The limit seems to be 99 spoilers per message.
            size = max(2, min(size, 10))

            # Fill board with blanks
            board = [[self.states['BLANK'] for _i in range(size)]for _j in range(size)]

            
            # Set bombs in board
            if bombs == -1:
                bomb_count = int(size*size*0.2)
            else:
                bomb_count = min(bombs, int(size*size*0.7))
            while bomb_count > 0:
                row = randint(0, size-1)
                column = randint(0, size-1)

                if board[row][column] == self.states['BLANK']:
                    board[row][column] = self.states['BOMB']
                    bomb_count -= 1

            

            # Set neighbouring bombs number
            for row in range(size):
                for column in range(size):
                    cell = board[row][column]
                    if cell != self.states['BOMB']:
                        neighbourgs = await self.count_neighborgs(board, size, row, column)
                        if neighbourgs > 0:
                            board[row][column] = self.states[neighbourgs]

            # Transform board to message
            for row in range(size):
                board[row] = "".join(board[row])

            message = "\n".join(board)

            return await ctx.send(message)

class RandomGames(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.category = "Fun"

        self.diceregex = re.compile(r'(\d+)d(\d+)([+-]\d+)?')

    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.command(
        name='coin',
        aliases=['moneda'],
        help='¡Lanza una moneda!'
    )
    async def throwcoin(self, ctx: commands.Context):
        coin = randint(0,1)
        embed = discord.Embed(
            title='Lanzando la moneda.',
            type='rich',
            description='¿Qué caerá?',
            color=discord.Colour.dark_orange()
        )
        embed.set_image(url='https://media2.giphy.com/media/6jqfXikz9yzhS/giphy.gif')
        message:discord.Message= await ctx.send(embed=embed)
        await asyncio.sleep(3)
        embed= discord.Embed(
            title=('Cara', 'Sello')[coin],
            type='rich',
            color = discord.Colour.dark_gold()
        )
        embed.set_image(url=('https://i.imgur.com/QAKxjWC.png', 'https://i.imgur.com/ceBFC9W.png')[coin])
        await message.edit(embed=embed)

    @commands.command(
        name='roll',
        aliases=['dado', 'dados'],
        help='¡Tira los dados!\nFormato: [numero de dados]d[numero de caras][± modificador]'
    )
    async def dados(self, ctx: commands.Context, throw: str):
        values = self.diceregex.findall(throw)[0]
        tiros = int(values[0])
        caras = int(values[1])
        mod = 0
        if values[2] != '':
            mod = int(values[2])
        assert 1 <= tiros <= 100
        assert caras >= 4

        valor_final = 0
        for _i in range(tiros):
            valor_final += randint(1, caras)

        await ctx.send(valor_final+mod)

    @dados.error
    async def dados_error(self, ctx: commands.Context, error):
        await ctx.send('Formato incorrecto\nFormato: (1 <= dados <= 100)d(caras >= 4)(±modificador)')


def setup(bot):
    bot.add_cog(Sweeper(bot))
    bot.add_cog(RandomGames(bot))