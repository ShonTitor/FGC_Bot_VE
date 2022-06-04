import requests
import json
import os
import base64
import io
from datetime import datetime

from PIL import Image

path = os.path.realpath(__file__)
path = os.path.abspath(os.path.join(path, os.pardir))

with open(os.path.join(path, "config.json"), "r") as f:
    config = json.loads(f.read())
    authToken = config["smashggAPIKey"]
    challonge_key = config["challongeAPIKey"]
    videogameIds = config["gameIds"]
    countryCode = config["countryCode"]
    top8er_api_url = config["top8er_api_url"]


# Cosas de smash gg
apiVersion = 'alpha'
url = 'https://api.smash.gg/gql/' + apiVersion
headers = {'Content-Type': 'application/json',
           'Authorization': 'Bearer '+authToken
           }

char_data = json.loads(requests.get(url="https://api.smash.gg/characters").content)
char_corrections = {
        "Pokemon Trainer": "Pokémon Trainer",
        "Mr. Game & Watch": "Mr Game & Watch",
        "Sheik / Zelda": "Sheik"
    }
char_data = char_data["entities"]["character"]
char_dict = {
              c["id"]:char_corrections.get(c["name"], c["name"])
              for c in char_data
              }
char_dict[-1] = "Random"

game_ids_dict = {
        1386: "ssbu",
        1: "melee",
        2: "p+",
        4: "ssb64",
        5: "ssbbminus"
    }


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

def scan_sgg(page=1, videogameIds=videogameIds, countryCode=countryCode) :
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
          events {
            slug
            videogame { id }
          }
        }
      }
    }
    '''
    variables = {
  	"page" : page,
        "perPage": 20,
        "videogameId": videogameIds,
        "countryCode": countryCode
    }
    payload = {"query" : query, "variables" : variables}
    response = requests.post(url=url, headers=headers, json=payload)
    data = json.loads(response.content)
    #print(data)
    #print('\n')
    try :
        events = [ event["slug"] for event in
                   filter( lambda e : e["videogame"]["id"] in videogameIds,
                          [ e for tournament in data["data"]["tournaments"]["nodes"]
                              for e in tournament["events"] ]
                         )
                 ]
        pass
    except :
        events = []
    return events

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
          videogame {id}
          tournament {
                        name
                        countryCode
                        slug
                        shortSlug
                        city
                        images {type url}
                      }

          standings(query: {
            page: 1
            perPage: 8
            sortBy: "standing"
          }){
            nodes{
              placement
              entrant{
                name
                participants {
                  user {
                    authorizations(types:TWITTER) {
                      externalUsername
                    }
                  }
                }
              }
            }
          }

            sets(page: 1, perPage: 11, sortType: MAGIC) {
                nodes {
                    games {
                        selections {
                            entrant {name}
                            selectionValue
                        }
                    }
                }
            }

        }
    	}
    '''
    payload = {"query" : query, "variables" : {"slug" : slug}}
    response = requests.post(url=url, headers=headers, json=payload)
    return json.loads(response.content)

def sgg_char_freq(sets):
    freq = {}

    for node in sets['nodes'] :
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
            key:sorted([(v, char_dict[k]) for k,v in value.items()], reverse=True)
            for key, value in freq.items()
            }

def sgg_data(slug) :
    data = sgg_query(slug)
    #print(data)
    data = data["data"]
    char_freq = sgg_char_freq(data["event"]["sets"])
    #print(char_freq)

    players = []
    for p in data["event"]["standings"]["nodes"] :
                name = p["entrant"]["name"]
                twi = None
                position = p["placement"]
                P = p["entrant"]["participants"]
                if len(p["entrant"]["participants"]) == 1 :
                    if P[0]["user"] and P[0]["user"]["authorizations"] :
                        twi = "@"+P[0]["user"]["authorizations"][0]["externalUsername"]
                players.append({"tag" : name,
                                "twitter" : twi,
                                "position": position,
                                "char": (char_freq.get(name, [(0, "Random")])[0][1], 0)
                                })

    event = data["event"]
    if event["tournament"]["countryCode"] :
        country = event["tournament"]["countryCode"]
    else : country = None
    name = event["tournament"]["name"] + " - " + event["name"]

    if event["tournament"]["shortSlug"] :
        link = "https://smash.gg/"+event["tournament"]["shortSlug"]
    else :
        link = "smash.gg/"+event["tournament"]["slug"]

    ttext = f"{event['tournament']['name']} - {event['name']}"
    btext = []
    if event["startAt"] :
        fecha = datetime.fromtimestamp(event["startAt"])
        fecha = fecha.strftime("%Y/%m/%d")
        btext.append(fecha)
    if event["tournament"]["city"] :
        ciudad = event["tournament"]["city"]
        btext.append(ciudad)
    btext.append(str(event["numEntrants"])+" Participants")
    btext = " - ".join(btext)

    datos = {
        "players" : players,
        "name" : name,
        "url" : link,
        "country" : country,
        "participants_number": event["numEntrants"],
        "game": game_ids_dict.get(event["videogame"]["id"], "idk"),
        "toptext": ttext,
        "bottomtext": btext
        }
    return datos

def format_data(data) :
    name = lambda x : x["twitter"] if x["twitter"] is not None else x["tag"]
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
    #print(json.dumps(data))
    response = requests.post(top8er_api_url,
                             data=data,
                             files= files)
    r = json.loads(response.content)
    return r

if __name__ ==  "__main__" :
    #slug = "tournament/frosty-faustings-xii-2020/event/under-night-in-birth-exe-late-st"
    #slug = "tournament/genesis-7-1/event/ultimate-singles"
    #slug = "tournament/super-smash-con-fall-fest/event/brawl-1v1-singles"
    #slug = "tournament/can-tv-melee-venezuela-5/event/melee-singles"
    #slug = "tournament/can-tv-8/event/melee-singles"
    #slug = "tournament/can-tv-melee-venezuela-7/event/melee-singles"
    #slug = "tournament/can-tv-melee-venezuela-5/event/melee-singles"
    #slug = "tournament/volver-al-melee/event/melee-singles"
    #slug = "tournament/smash-pro-league-8/event/smash-64-singles"
    #slug = "tournament/can-tv-10/event/melee-singles"
    slug = "tournament/season-finale-1/event/singles"
    #slug = "tournament/smash-pro-league-14/event/ultimate-singles"

    events = scan_sgg()
    #slug = events[0]
    print(check_sgg(slug))
    d = sgg_data(slug)
    print(format_data(d))
    top8er = get_top8er(d)
    if "error" in top8er:
        print(top8er["error"])
    else:
        base64_img = base64.b64decode(top8er["base64_img"])
        buffer = io.BytesIO(base64_img)
        img = Image.open(buffer)
        img.show()
        input()

    #slug = "ACTIVBBCF"
    #print(check_challonge(slug))
    #d = challonge_data(slug)
    #print(format_data(d))

