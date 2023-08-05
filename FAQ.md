# Preguntas Frecuentes FGC Bot VE

Esta guía tiene como objetivo aclarar ciertos puntos importantes sobre el funcionamiento del bot de twitter [FGC Bot VE](https://twitter.com/FGC_Bot_VE).

## ¿Qué juegos soporta FGC Bot VE?

Actualmente FGC Bot VE busca en start.gg torneos presenciales en Venezuela de:

### Platform Fighters

- Super Smash Bros. Melee
- Project M
- Super Smash Bros. for Wii U
- Super Smash Bros.
- Super Smash Bros. Brawl
- Super Smash Bros. Ultimate
- Rivals of Aether
- MultiVersus
- Brawlhalla
- Project+
- Super Smash Flash 2

### Fighters tradicionales

- Street Fighter 6
- Street Fighter V
- Street Fighter III: 3rd Strike
- Mortal Kombat 11
- TEKKEN 7
- Power Rangers: Battle for the Grid
- Among Us Arena
- The King of Fighters XV
- The King of Fighters '98 Ultimate Match Final Edition
- The King of Fighters 2002: Unlimited Match
- The King of Fighters XIII
- Killer Instinct
- Mortal Kombat X
- Mortal Kombat XL
- Mortal Kombat 1
- SAMURAI SHODOWN

### Airdashers/Anime fighters

- Guilty Gear: Strive
- Guilty Gear XX Accent Core Plus R
- BlazBlue: Central Fiction
- Skullgirls: 2nd Encore
- Guilty Gear Xrd REV2
- DRAGON BALL FighterZ
- Persona 4 Arena Ultimax
- Under Night In-Birth Exe:Late[cl-r]
- Ultimate Marvel vs Capcom 3
- Vampire Savior
- BlazBlue: Cross Tag Battle
- Granblue Fantasy: Versus
- Melty Blood Actress Again Current Code
- Melty Blood: Type Lumina
- DNF Duel
- Akatsuki Blitzkampf: Ausf Achse
- Idol Showdown
- Marvel vs. Capcom: Infinite

Si crees que hay algún otro torneo que merece estar aquí, no dudes en hacérmelo saber para agregarlo.

## ¿Qué sitios para hostear torneos soporta FGC Bot VE?

FGC Bot VE soporta solamente start.gg y challonge.

## ¿Cómo hago que mi torneo de start.gg aparezca en FGC Bot VE?

Es necesario que el torneo tenga como país Venezuela, que sea de uno de los juegos soportados y que esté configurado como público y "discoverable".
Esto último se puede cambiar en el "dashboard" o "panel de control" de start gg. Sabrás que tu torneo fue correctamente encontrado por el bot si aparece en un tweet de "Nuevo torneo encontrado". Si aún luego de configurarlo de esta manera el torneo no aparece, puedes contactarme por [twitter](https://twitter.com/Riokaru), discord (riokaru) para agregarlo manualmente.

![discoverable](https://user-images.githubusercontent.com/39103403/158497713-a8603177-f383-4228-8d3d-3d90a75bd91c.png)

## ¿Cómo hago que mi torneo de challonge aparezca en FGC Bot VE?

La API de challonge no es tan completa como la de start.gg, por lo cual el bot no puede encontrar torneos de challonge por su cuenta.
Si quieres que tu torneo aparezca, puedes contactarme por [twitter](https://twitter.com/Riokaru), discord (riokaru).

## ¿Cómo hago que mi torneo tenga un banner de top 8 en FGC Bot VE?

Acualmente esta funcionalidad solo está disponible para torneos de start.gg y solo para torneos de los siguientes juegos:

- Super Smash Bros. Melee
- Super Smash Bros. Ultimate
- Rivals of Aether
- Street Fighter 6
- Guilty Gear: Strive
- BlazBlue: Central Fiction

Para que el bot genere el banner, necesita información de los personajes de cada jugador. 

Esta información se toma de dos fuentes. La primera son los sets de start.gg. Estos datos se introducen al momento de reportar los matches de un set (ejemplo abajo). Actualmente el bot revisa los sets reportados y pone en el banner solo al personaje más frecuente.

![sets](https://user-images.githubusercontent.com/39103403/158500391-14843768-a93f-4528-aba8-e0561edfe935.png)

La segunda son los datos del [Censo de la FGC Venezolana 2023](https://twitter.com/Riokaru/status/1664281778654429185) Primero se intenta buscar según el perfil de start.gg. Si el player no llenó esta info o la llenó incorrectamente, se intenta buscar según el tag del jugador. Esto se hace con [fuzzy search](https://en.wikipedia.org/wiki/Approximate_string_matching) de modo que si el tag en el censo es suficientemente parecido al tag en start gg, hará la asociación. Por ejemplo, si el tag en el censo es "morrocoYo " y en start.gg es "morrocoYo" la asociación puede hacerse sin problemas. Si no se encuentra al personaje por ninguno de estos métodos, se deja con una imagen placeholder (Ejemplo: Sandbags en el caso de smash).

## Llegué a un top 8 y el bot no puso mi twitter

SmashResultsVE toma la cuenta de twitter asociada a start gg. Si quieres que aparezca en el tweet en el futuro debes conectar tu cuenta de twitter a tu cuenta de start.gg y habilitar la opción "Display on profile". Si no se encuentra una cuenta de twitter asociada, se intenta buscar en los datos del censo con el mismo método descrito arriba.

![twitter](https://user-images.githubusercontent.com/39103403/158501301-ea7eda88-c7a6-4cb8-85f2-ae0e9296b3ac.png)

## Llegué a un top 8 y el bot no puso mi personaje/twitter o puso los de otra persona

FGC Bot VE hace lo mejor que puede con los datos que tiene para tratar de identificar correctamente a los players. Como los datos están incompletos y se utilizan técnicas de búsqueda aproximada, pueden ocurrir errores. La mejor manera de garantizar que el bot tome tus datos correctamente es llenar el censo y poner el enlace al perfil de start.gg correctamente.

![image_2023-08-05_110044286](https://github.com/ShonTitor/SmashResultsVE/assets/39103403/77f387a8-76ed-45fc-82d0-edb14b6bb584)
