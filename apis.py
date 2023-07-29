import requests
import json
import csv
import os
import base64
import io
import time
import random
from datetime import datetime

from PIL import Image
from thefuzz import fuzz
from thefuzz import process

path = os.path.realpath(__file__)
path = os.path.abspath(os.path.join(path, os.pardir))

with open(os.path.join(path, "config.json"), "r") as f:
    config = json.loads(f.read())
    authToken = config["smashggAPIKey"]
    challonge_key = config["challongeAPIKey"]
    videogameIds = config["gameIds"]
    countryCode = config["countryCode"]
    top8er_api_url = config["top8er_api_url"]

with open(os.path.join(path, "config_games.json"), "r") as f:
    config_games = json.loads(f.read())

# Cosas de smash gg
apiVersion = 'alpha'
url = 'https://api.smash.gg/gql/' + apiVersion
headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer '+authToken
}

char_data = json.loads(requests.get(url="https://api.smash.gg/characters").content)

game_ids_dict = {int(key):value["top8er_name"] for key, value in config_games.items()}

char_data = char_data["entities"]["character"]

char_corrections = {
    int(key):value.get("char_corrections", {})
    for key, value in config_games.items()
}

char_dict = {
    key:{
        c["id"]:char_corrections[key].get(c["name"], c["name"])
        for c in char_data
        if c["videogameId"] == key
    }
    for key in game_ids_dict
}

discriminator_char_fallback = {}
tag_char_fallback = {}

discriminator_twitter = {}
tag_twitter = {}

for gameId, values in config_games.items():
  game = values["top8er_name"]

  discriminator_char_fallback[game] = {}
  tag_char_fallback[game] = {}

  discriminator_twitter[game] = {}
  tag_twitter[game] = {}

  sgg_discriminator_col_index = values["sgg_discriminator_col_index"]
  name_col_index = values["name_col_index"]
  twitter_col_index = values["twitter_col_index"]
  char_col_indexes = values["char_col_indexes"]
  color_col_indexes = values["color_col_indexes"]

  with open(os.path.join(path, "fallback_data", f"{game}.csv"), "r", encoding="utf-8") as f:
    csv_reader = csv.reader(f, delimiter=',')
    for row in csv_reader:
      chars = [row[i] for i in char_col_indexes if row[i] != ""]
      colors = [int(row[i]) for i in color_col_indexes]
      colors += [0 for _ in range(len(chars)-len(colors))]
      characters = [(chars[i], colors[i]) for i in range(len(chars))]
      twitter = row[twitter_col_index] or None

      discriminator_char_fallback[game][row[sgg_discriminator_col_index]] = characters
      tag_char_fallback[game][row[name_col_index]] = characters

      discriminator_twitter[game][row[sgg_discriminator_col_index]] = twitter
      tag_twitter[game][row[name_col_index]] = twitter

game_chars = {}
for game in game_ids_dict.values():
    game_data_url = f"{top8er_api_url}/game_data/{game}/"
    r = requests.get(game_data_url)
    if r.status_code == 200:
      game_data = json.loads(r.content)
      characters = game_data["characters"]
      game_chars[game] = characters
    time.sleep(0.1)

def check_challonge(slug) :
    headers = { 'User-Agent': 'Top8er' }

    url = "https://api.challonge.com/v1/tournaments/"+slug+".json?api_key="+challonge_key+"&include_participants=1"
    response = requests.get(url, headers=headers)
    datos = json.loads(response.content)
    #datos["tournament"]["complete_at"]
    if "tournament" in datos :
        return datos["tournament"]["state"] == "complete"
    else :
        return None

def get_challonge_username(player_dict):
    keys = ["display_name_with_invitation_email_address", "display_name", "username", "name"]
    for key in keys:
        if key in player_dict:
            return player_dict[key]

def challonge_data(slug) :
    headers = { 'User-Agent': 'SmashResultsVE' }

    url = "https://api.challonge.com/v1/tournaments/"+slug+".json?api_key="+challonge_key+"&include_participants=1"
    #print(url)
    response = requests.get(url, headers=headers)
    datos = json.loads(response.content)
    if "tournament" in datos :
        datos = datos["tournament"]
    else :
        return False

    players = [p["participant"] for p in datos["participants"]]
    if all(not p["final_rank"] is None for p in players) :
        players = sorted(players, key=lambda p: p["final_rank"])
    players = players[:8]
    players = [{"tag": get_challonge_username(p),
                "twitter": None,
                "position": p["final_rank"],
                "char": None
                }
               for p in players]

    url = datos['full_challonge_url']

    datos = {
        "players" : players,
        "name" : datos["name"],
        "url" : url,
        "country" : None,
        "participants_number": datos["participants_count"]
        }
    return datos

def scan_sgg(page=1, videogameIds=videogameIds, countryCode=countryCode, modo_arrecho=False) :
    query = '''
    query Torneitos($page: Int!, $perPage: Int!, $videogameId: [ID]!, $countryCode: String!) {
      tournaments(query: {
        page: $page
        perPage: $perPage
        sortBy: "startAt desc"
        filter: {
          countryCode: $countryCode
          videogameIds: $videogameId
          upcoming: true
        }
      }) {
        nodes {
          name
          city
          postalCode
          slug
          shortSlug
          owner {
            discriminator
          }
          events {
            slug
            videogame { id }
          }
        }
      }
    }
    '''

    if modo_arrecho:
        query = query.replace("upcoming: true", "")

    variables = {
    "page" : page,
        "perPage": 20,
        "videogameId": videogameIds,
        "countryCode": countryCode
    }
    payload = {"query" : query, "variables" : variables}
    response = requests.post(url=url, headers=headers, json=payload)
    data = json.loads(response.content)

    if "data" not in data:
        print(data)
        return None

    #print(data)
    #print('\n')
    try :
        tournaments = [
            t for t in data["data"]["tournaments"]["nodes"]
            if t["owner"]["discriminator"] not in config.get("sgg_discriminator_banlist", [])
        ]

        events = [ event["slug"] for event in
                   filter( lambda e : e["videogame"]["id"] in videogameIds,
                          [ e for tournament in tournaments
                              for e in tournament["events"] ]
                         )
                 ]

        results = {
            "events": events,
            "tournaments": tournaments
        }
    except Exception:
        return None

    return results

def check_sgg(slug) :
    query = '''
    query CompletedQuery($slug: String) {
        event(slug: $slug) {
          numEntrants
          state
        }
    }
    '''
    payload = {"query" : query, "variables" : {"slug" : slug}}
    response = requests.post(url=url, headers=headers, json=payload)
    if response.status_code != 200:
        print("CHECK_SGG:", response.content)
        time.sleep(10)
    event = json.loads(response.content)["data"]["event"]
    #print(event)
    if event is None :
      return None
    if event["numEntrants"] \
       and event["numEntrants"] > 0 \
       and event["state"] == "COMPLETED" :
            return True
    else :
        return False

def sgg_query(slug) :
    query = '''
    query StandingsQuery($slug: String) {
      event(slug: $slug) {
        id
        name
        numEntrants
        state
        startAt
        videogame {
          id
        }
        tournament {
          name
          countryCode
          slug
          shortSlug
          city
          images {
            type
            url
          }
        }
        standings(query: {page: 1, perPage: 8, sortBy: "standing"}) {
          nodes {
            placement
            entrant {
              name
              participants {
                user {
                  discriminator
                  authorizations(types: TWITTER) {
                    externalUsername
                  }
                }
              }
            }
          }
        }
      }
    }
    '''
    payload = {"query" : query, "variables" : {"slug" : slug}}
    response = requests.post(url=url, headers=headers, json=payload)
    print(response.status_code)
    return json.loads(response.content)

def sgg_sets_query(slug) :
    query = '''
    query SetsQuery($slug: String, $page: Int) {
      event(slug: $slug) {
        sets(page: $page, perPage: 50, sortType: MAGIC) {
          nodes {
            games {
              selections {
                entrant {
                  name
                }
                selectionValue
              }
            }
          }
        }
      }
    }
    '''
    sets = []
    page = 1
    while True:
        prev = len(sets)
        payload = {"query" : query, "variables" : {"slug" : slug, "page": page}}
        response = requests.post(url=url, headers=headers, json=payload)
        data = json.loads(response.content)
        new_sets = data["data"]["event"]["sets"]["nodes"]
        if len(new_sets) == 0:
            break
        sets += new_sets
        time.sleep(1)
        page += 1
    
    return sets

def sgg_char_freq(sets, gameId):
    freq = {}

    for node in sets:
        if node["games"] is None : continue
        for game in node["games"] :
            if game["selections"] :
                for selection in game["selections"] :
                    player = selection["entrant"]["name"]
                    char = selection["selectionValue"]
                    if player in freq :
                        if char in freq[player] :
                            freq[player][char] += 1
                        else :
                            freq[player][char] = 1
                    else :
                        freq[player] = {char : 1}
    return {
      key:sorted([(v, char_dict.get(gameId, {}).get(k, k)) for k,v in value.items()], reverse=True)
      for key, value in freq.items()
    }

def sgg_data(slug) :
    data = sgg_query(slug)
    #print(data)
    data = data["data"]
    time.sleep(1)
    sets = sgg_sets_query(slug)
    gameId = data["event"]["videogame"]["id"]
    game = game_ids_dict.get(gameId)
    allow_random = False
    random_substitutes = None
    if game:
        allow_random = config_games[str(gameId)].get("allow_random", False)
        random_substitutes = config_games[str(gameId)].get("random_image_urls")
    char_freq = sgg_char_freq(sets, gameId)
    #print(char_freq)

    players = []
    for p in data["event"]["standings"]["nodes"] :
      name = p["entrant"]["name"]
      twi = None
      position = p["placement"]
      tag = name
      if " | " in tag:
          tag = tag.split(" | ")[-1]

      P = p["entrant"]["participants"]

      userId = None
      if len(p["entrant"]["participants"]) >= 1 and P[0]["user"]:
          userId = P[0]["user"]["discriminator"]

      if game and userId:
          twi = discriminator_twitter[game].get(userId)

      if not twi and len(p["entrant"]["participants"]) == 1 :
        if P[0]["user"] and P[0]["user"]["authorizations"] :
          twi = "@"+P[0]["user"]["authorizations"][0]["externalUsername"]

      if game and not twi:
          print("toca fuzzy (twitter)", name)
          p = process.extract(tag, tag_twitter[game].keys(), limit=1, scorer=fuzz.ratio)
          if len(p) > 0 and p[0][1] >= config.get("player_fuzz_tolerance", 70):
              twi = tag_twitter[game][p[0][0]]
          print(p, twi)

      if not twi:
          twi = " "
      
      char = char_freq.get(name, [(0, None)])[0][1]

      possible_chars = game_chars[game] if game else []
      if game and char is not None and char not in possible_chars and len(possible_chars) > 0:
          print("toca fuzzy con el personaje", char)
          p = process.extract(char, possible_chars, limit=1)
          print(f"{char} => {p[0][0]}")
          char = p[0][0]
          
      if len(possible_chars) == 0:
          char = None

      if char is not None:
          char = (char, 0)

      char_fallback_dict = discriminator_char_fallback[game] if game else {}
      fallback = char_fallback_dict.get(userId, [])

      if game and fallback == []:
          print("toca fuzzy", name)
          p = process.extract(tag, tag_char_fallback[game].keys(), limit=1, scorer=fuzz.ratio)
          if len(p) > 0 and p[0][1] >= config.get("player_fuzz_tolerance", 70):
              fallback = tag_char_fallback[game][p[0][0]]
          print(p)

      print("FALLBACK", name, fallback)

      if char is None and fallback:
          char = fallback[0]

      if char is not None and fallback:
          for c,s in fallback:
              if c == char[0]:
                  char = (c,s)
                  break

      if char is None and allow_random:
          char = ("Random", 0)
    
      if char is None and random_substitutes:
        char = random.choice(random_substitutes)

      players.append({
        "tag" : name,
        "twitter" : twi,
        "position": position,
        "char": char
      })

    event = data["event"]
    if event["tournament"]["countryCode"] :
        country = event["tournament"]["countryCode"]
    else : country = None
    name = event["tournament"]["name"] + " - " + event["name"]

    if event["tournament"]["shortSlug"] :
        link = "https://www.start.gg/"+event["tournament"]["shortSlug"]
    else :
        link = "https://www.start.gg/"+event["tournament"]["slug"]

    ttext = f"{event['tournament']['name']} - {event['name']}"
    btext = []
    if event["startAt"] :
        fecha = datetime.fromtimestamp(event["startAt"])
        fecha = fecha.strftime("%Y/%m/%d")
        btext.append(fecha)
    if event["tournament"]["city"] :
        ciudad = event["tournament"]["city"]
        btext.append(ciudad)
    btext.append(str(event["numEntrants"])+" Participantes")
    btext = " - ".join(btext)

    datos = {
        "players" : players,
        "name" : name,
        "url" : link,
        "country" : country,
        "participants_number": event["numEntrants"],
        "game": game_ids_dict.get(event["videogame"]["id"], "idk"),
        "toptext": ttext,
        "bottomtext": btext,
        "gameId": gameId
        }
    return datos

def format_data(data) :
    #name = lambda x : x["twitter"] if x["twitter"] is not None else x["tag"]
    def name(x):
        tag = x["tag"]
        if len(tag) > 18 and " | " in tag:
            tag = tag.split(" | ", 1)[1]
        if len(tag) > 18:
            tag = tag[:15] + "..."
        return tag
    
    players = [f"{p['position']}. {name(p)}"
                for p in data["players"]]
    players = "\n".join(list(players))

    text = "Top {0} {1}\n{2} participantes\n\n".format(
                                    len(data["players"]),
                                    data["name"],
                                    data["participants_number"])
    text += players
    text += "\n\nBracket:\n" + data["url"]

    return text

def is_sgg(slug) :
    return slug.startswith("tournament/")

def is_challonge(slug) :
    return not is_sgg(slug)

def check_event(slug) :
    if is_sgg(slug) :
      return check_sgg(slug)
    elif is_challonge(slug) :
      return check_challonge(slug)

def event_data(slug) :
    if is_sgg(slug) :
      return sgg_data(slug)
    elif is_challonge(slug) :
      return challonge_data(slug)

def to_top8er_dict(orig_data):
    data = {
            "game": orig_data["game"],
            "lcolor1": "#1ACACA",
            "lcolor2": "#1ACACA",
            "ttext": orig_data["toptext"],
            "btext": orig_data["bottomtext"],
            "url": orig_data["url"],
            "fontt": "auto",
            "fcolor1": "#ffffff",
            "fscolor1": "#000000",
            "fcolor2": "#ffffff",
            "fscolor2": "#000000",
            "blacksquares": True,
            "darken_bg": True,
            "charshadow": True
            }
    for i in range(1,9):
        data[f"player{i}_name"] = orig_data["players"][i-1]["tag"]
        data[f"player{i}_twitter"] = orig_data["players"][i-1]["twitter"] or " "
        data[f"player{i}_char"] = orig_data["players"][i-1]["char"][0]
        data[f"player{i}_color"] = orig_data["players"][i-1]["char"][1]
        data[f"player{i}_flag"] = "None"
        data[f"player{i}_custom_flag"] = None
        data[f"player{i}_portrait"] = None
    return data

def get_top8er(data):
    bg_path = os.path.join(path, f'bg_{data["game"]}.png')
    files = {'background': open(bg_path,'rb')}
    data = to_top8er_dict(data)
    response = requests.post(f"{top8er_api_url}/salu2?format=json",
                             data=data,
                             files= files)
    r = json.loads(response.content)
    return r

def get_top8er_new(data):
    players = []
    for player in data["players"]:
        p = {
            "name": player["tag"],
            "social": player["twitter"],
            "character": [player["char"] if player["char"] is not None else None, None, None],
            "flag": [None, None]
        }
        players.append(p)
    options = {
        "toptext": data["toptext"],
        "url": data["url"],
        "bottomtext": data["bottomtext"],
        "layoutcolor": "#df2c3b",
        "fontcolor": "#ffffff",
        "fontcolor2": "#ffffff",
        "fontshadowcolor": "#000000",
        "fontshadowcolor2": "#000000",
        "mainfont": None,
        "blacksquares": True,
        "charshadow": True,
        "textshadow": True,
        "darkenbg": False,
        "layout": True
    }

    game = data['game']
    gameId = None
    for gid, gameName in game_ids_dict.items():
        if gameName == game:
            gameId = str(gid)
            break
    
    if gameId:
        options.update(config_games[gameId].get("top8er_options", {}))

    request_data = {
        "players": players,
        "options": options
    }

    response = requests.post(f"{top8er_api_url}/generate/top8er-2023/{data['game']}/",
                             json=request_data)
    if response.status_code != 200:
        print(response.content)
        return None
    r = json.loads(response.content)
    return r

if __name__ ==  "__main__" :
    slug = "tournament/phoenix-rise/event/ultimate-singles"
    slug = "tournament/phoenix-rise/event/melee-singles"
    slug = "tournament/phoenix-rise/event/guilty-gear-strive"
    slug = "tournament/phoenix-rise/event/rivals-singles"

    events = scan_sgg()
    #slug = events[0]
    print(check_sgg(slug))
    d = sgg_data(slug)
    print(format_data(d))
    #top8er = get_top8er(d)
    top8er = get_top8er_new(d)
    if top8er is None:
        print(top8er)
    else:
        base64_img = base64.b64decode(top8er["base64_img"])
        buffer = io.BytesIO(base64_img)
        img = Image.open(buffer)
        img.show()
        img.save(os.path.join("debug_images", f"{slug.replace('/', '_')}.png"), optimize=True)