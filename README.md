VidalBot
========

[![Invitación Discord](https://discordapp.com/api/guilds/841931012765122591/widget.png)](https://discord.gg/fsV6TkvCjk)

Bot experimental para Discord™. Hecho con [discord.py](https://github.com/Rapptz/discord.py)


Instalación
-----------
Este bot requiere Python 3.8+

---
Aunque no es estrictamente necesario, se recomienda crear un entorno virtual para el bot.
```
python3 -m venv venv
```
Para activar el entorno virtual, debemos ejecutar lo siguiente dependiendo del ecosistema en el que se está usando

|Plataforma|Shell          |Comando para activar el entorno virtual|
|----------|---------------|---------------------------------------|
|POSIX     |bash/zsh       |``$ source <venv>/bin/activate``       |
|          |fish           |``$ source <venv>/bin/activate.fish``  |
|          |csh/tcsh       |``$ source <venv>/bin/activate.csh``   |
|          |PowerShell Core|``$ <venv>/bin/Activate.ps1``          |
|Windows   |cmd.exe        |``C:\> <venv>\Scripts\activate.bat``   |
|          |PowerShell     |``PS C:\> <venv>\Scripts\Activate.ps1``|
---
Se deben instalar las dependencias del bot, esto se puede hacer con el siguiente comando
```
python3 -m pip install -r requirements.txt
```
Se debe hacer una copia de ``config.py.template`` y renombrarla a ``config.py``

Para ejectuar el bot, es necesario contar con un TOKEN de bot Discord. Este se puede conseguir en https://discord.com/developers/applications

Una vez se tenga ese token, hay que reemplazar el valor por defecto en ``config.py``. Desde ahí también se puede cambiar el prefijo que utilizará el bot.

Terminado todo esto, se puede ejecutar el bot con 
```
python3 bot.py
```
---

Comandos disponibles
--------------------

Nota: Los comandos actuales se pueden consular con el comando ``.help``
```
AdminMisc:
  dm           
  message      
  ping         Muestra la latencia entre el bot y los servidores de Discord.
  prefix       Visualiza y (solo administrador) cambia el prefijo del bot en ...
Akinator_Game:
  akinator     Juega a Akinator!
CasosCovidChile:
  covid        Solicita y administra la recolección de datos sobre el COVID-1...
HoroscopoTiaYoli:
  horoscopo    ¡Obtenga su horóscopo de la Tía Yoli!
ImageManipulation:
  weezer       Convierte un avatar en una portada de Weezer
KanyeQuotes:
  kanye        Frases de Kanye West
MiscCommands:
  emoji        Obtén la imagen de un emoji.
  rate         Califica un usuario o texto
RandomAnimals:
  bird         Imágenes de aves
  bunny        Imágenes de conejos
  cat          Imágenes de gatos
  dog          Imágenes de perros
  duck         Imágenes de patos
  fox          Imágenes de zorros
  hyena        Imágenes de hienas
  shiba        Imágenes de Shiba Inus
RandomGames:
  coin         ¡Lanza una moneda!
  roll         ¡Tira los dados!
Sweeper:
  sweeper      ¡Juega a BuscaMinas!
Wate:
  setwates     Establece directamente la cantidad de wates de algún usuario
  wate         
  waterank     Visualiza el ranking de wates.
  wates        Ver cuantos wates se le han pegado a alguien
```

