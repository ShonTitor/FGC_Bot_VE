# SmashResultsVE
This is a Twitter bot that publishes Venezuelan Super Smash Bros Tournaments results using the [smash.gg ](https://smash.gg/) API. You can see it working [here](https://twitter.com/SmashResultsVe). The tweet format was inspired by [Lunar Phase](https://github.com/lunar-phase/smashgg-results)

![alt text](https://i.imgur.com/KXaZhIc.png "Smash Twitter Bot")

## Usage

Create a file named `apikeys.json` and enter your keys with the following format:
```
{
    "smashgg_auth_token" : ...,
    "twitter_consumer_key" : ...,
    "twitter_consumer_secret" : ...,
    "twitter_access_token_key" : ...,
    "twitter_access_token_secret" : ...
}
```

Then simply run `python SmashResultsVE.py` or `python3 SmashResultsVE.py` according to your case.

The script "scans" for upcoming Venezuelan Super Smash Bros tournaments every 10 minutes and posts results of finished events. If an event is left unfinished 6 days after its start date it is deemed to be over and is no longer considered.
