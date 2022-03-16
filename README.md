# SmashResultsVE
This is a Twitter bot that publishes Venezuelan Super Smash Bros Tournaments results using the [smash.gg ](https://smash.gg/) API. You can see it working [here](https://twitter.com/SmashResultsVe). The tweet format was inspired by [Lunar Phase](https://github.com/lunar-phase/smashgg-results)

![alt text](https://i.imgur.com/X8HJaWr.png "Smash Twitter Bot")

## Usage

Create a file named `config.json` and enter your keys with the following format:
```
{
    "gameIds": [1,2,3,4,5,1386],
    "countryCode": "VE",
    "db_file": "gg.db",
    "top8er_api_url": "https://www.top8er.com/api/salu2?format=json",
    "challongeAPIKey": ...,
    "smashggAPIKey": ...,
    "twitter_consumer_key": ...,
    "twitter_consumer_secret": ...,
    "twitter_access_token_key": ...,
    "twitter_access_token_secret": ...
}
```

Enter your keys and options to your liking. The gameIds correspond to smash.gg game ids, a full list can be found [here](https://api.smash.gg/videogames). 
Then simply run `python bot.py` or `python3 bot.py` depending on your installation. You can also the run `shell.py` script to interact with the database (add tournaments to the queue manually, see pending tournaments). 

The script periodically looks up upcoming venezuelan (or whichever country correspond to the value of `countryCode` in the `config.json` file) Super Smash Bros (or whichever games that correspond to the game ids) tournaments on smash gg and posts results of finished tournaments. Challonge tournaments won't be looked up, but can be added manually by using `shell.py`. For Super Smash Bros Ultimate and Super Smash Bros Melee, the script will include a top 8 graphic made using the [top8er.com](http://www.top8er.com) API. Keep in mind the top8er API is still in development and might change without previous notice.
