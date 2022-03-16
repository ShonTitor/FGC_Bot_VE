# Preguntas Frecuentes SmashResultsVE

Esta guía tiene como objetivo aclarar ciertos puntos importanetes sobre el funcionamiento del bot de twitter [SmashResultsVE](https://twitter.com/SmashResultsVe).

## ¿Qué juegos soporta SmashResultsVE?

Actualmente SmashResultsVE busca en smash.gg torneos de:
- Super Smash Bros (64)
- Super Smash Bros Melee
- Super Smash Bros Brawl
- Project M
- Super Smash Bros for Wii U
- Super Smash Bros Ultimate

## ¿Qué sitios para hostear torneos soporta SmashResultsVE?

SmashResultsVE soporta solamente smash.gg y challonge.

## ¿Cómo hago que mi torneo de smash.gg aparezca en SmashResultsVE?

Es necesario que el torneo tenga como país Venezuela, que sea de uno de los juegos soportados y que esté configurado como público y "discoverable".
Esto último se puede cambiar en el "dashboard" o "panel de control" de smash gg.

![discoverable](https://user-images.githubusercontent.com/39103403/158497713-a8603177-f383-4228-8d3d-3d90a75bd91c.png)

## ¿Cómo hago que mi torneo de challonge aparezca en SmashResultsVE?

La API de challonge no es tan completa como la de smash.gg, por lo cual el bot no puede encontrar torneos de challonge por su cuenta.
Si quieres que tu torneo aparezca, puedes contactarme por [twitter](https://twitter.com/Riokaru), discord (Riokaru#7131) o mensaje privado en FB para que lo agregue manualmente.

## ¿Cómo hago que mi torneo tenga un banner de top 8 en SmashResultsVE?

Acualmente esta opción solo está disponible para torneos de smash.gg y solo para torneos de Super Smash Bros Ultimate y Super Smash Bros Melee.
Para que el bot genere el banner, necesita información de los personajes de cada jugador. En smash gg esto se hace al momento de reportar los matches de un set (ejemplo abajo).
Actualmente el bot revisa solo los últimos 11 sets reportados (esto probablemente será ampliado en el futuro) y pone en el banner al personaje más frecuente.

![sets](https://user-images.githubusercontent.com/39103403/158500391-14843768-a93f-4528-aba8-e0561edfe935.png)

## Llegué a un top 8 y el bot no puso mi twitter o lo puso mal

SmashResultsVE toma la cuenta de twitter asociada a smash gg. Si quieres que aparezca en el tweet en el futuro debes conectar tu cuenta de twitter a tu cuenta de smash.gg
y habilitar la opción "Display on profile".

![twitter](https://user-images.githubusercontent.com/39103403/158501301-ea7eda88-c7a6-4cb8-85f2-ae0e9296b3ac.png)

