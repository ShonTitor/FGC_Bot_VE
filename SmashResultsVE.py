import requests, json, time, twitter, os, datetime

os.chdir(os.path.dirname(os.path.realpath(__file__)))

def scan_VE() :
    query = '''
    query Torneitos($cCode: String!, $perPage: Int!, $videogameId: [ID]!, $sDate: Timestamp) {
      tournaments(query: {
        perPage: $perPage
        sortBy: "startAt asc"
        filter: {
          countryCode: $cCode,
          videogameIds : $videogameId
          afterDate: $sDate
        }
      }) {
        nodes {
          slug
        }
      }
    }
    '''
    variables = {
    "cCode": "VE",
    "perPage": 20,
    "videogameId": gameIds_smash,
    "sDate": int(time.time())
    }
    payload = {"query" : query, "variables" : variables}
    response = requests.post(url=url, headers=headers, json=payload)
    a = json.loads(response.content)
    try :
        A = [b["slug"][11:] for b in a["data"]["tournaments"]["nodes"]]
    except :
        A = []
    return A

def get_by_slug(slug) :
    query = '''
    query StandingsQuery($slug: String) {
      tournament(slug: $slug){
        id
        name
        slug
        startAt
        endAt
        events {
          id
          name
          slug
          numEntrants
          state
          videogame {id}
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
        }
      }
    }
    '''
    payload = {"query" : query, "variables" : {"slug" : slug}}
    response = requests.post(url=url, headers=headers, json=payload)
    return json.loads(response.content)

def resultados(torneo) :
    S = []
    complete = True

    for event in torneo["events"] :
        if event["state"] != "COMPLETED" :
            complete = False
            continue
        elif str(event["id"]) in done :
            continue
        elif not event["videogame"]["id"] in gameIds_smash :
            printl("esto no es smash: ", event["videogame"]["id"])
            continue
        
        s = "{}\n{} - {} participantes\n\n".format(
            torneo["name"],
            event["name"],
            event["numEntrants"])
        for p in event["standings"]["nodes"] :
            s += "{}. {}".format(
                p["placement"],
                p["entrant"]["name"])
            P = p["entrant"]["participants"]
            if len(P) == 1 :
                #P[0]["player"]["twitterHandle"] = None
                if P[0]["user"] and P[0]["user"]["authorizations"] :
                    s += " (@"+P[0]["user"]["authorizations"][0]["externalUsername"]+")"
            s += "\n"
        lawea = "\nhttps://smash.gg/{}/events/{}/standings".format(
            torneo["slug"],
            event["slug"].split("/")[-1])
        if len(s) + 30 <= 280 : s += lawea
        S.append(s)
        done.append(str(event["id"]))

    # Si pasan 6 dias se da por completado
    if int(time.time()) - int(torneo["endAt"]) > 518400 :
        printl("Alguien dejó un bracket mocho: "+torneo["name"])
        complete = True
    if complete :
        slug = torneo["slug"][11:]
        pendiente.remove(slug)
        for event in torneo["events"] :
            if str(event["id"]) in done :
                done.remove(str(event["id"]))
        try :
            r = "-".join(slug.split("-")[:-1])
            if r in recurrentes :
                slut = r+"-"+str(int(slug.split("-")[-1])+1)
                if not slut in pendiente :
                    pendiente.append(slut)
        except :
            pass
    return S

def printl(*args) :
    s = ""
    for i in args :
        s += str(i) + " "
    s = datetime.datetime.now().strftime('%d-%b-%G-%I:%M%p')+": "+s
    print(s)
    with open("output.log", "a", encoding="utf-8") as f :
        f.write(s+"\n")

if __name__ == '__main__' :
    f = open("apikeys.json", "r")
    apikeys = f.read()
    f.close()
    apikeys = json.loads(apikeys)

    # Cosas de smash gg
    authToken = apikeys["smashgg_auth_token"]
    apiVersion = 'alpha'
    url = 'https://api.smash.gg/gql/' + apiVersion
    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer '+authToken
               }

    # Cosas de twitter
    twitter_api = twitter.Api(consumer_key = apikeys["twitter_consumer_key"],
                      consumer_secret = apikeys["twitter_consumer_secret"],
                      access_token_key = apikeys["twitter_access_token_key"],
                      access_token_secret = apikeys["twitter_access_token_secret"])

    gameIds_smash = [1,2,3,4,5,1386]
    recurrentes = []

    pendiente = []
    torneos = []
    done = []
    open("pendiente.txt","a").close()
    open("done_events.txt","a").close()
    
    while True :
        try :
            with open("pendiente.txt","r") as f :
                pendiente = f.read().split("\n")
                if "" in pendiente : pendiente.remove("")

            with open("done_events.txt","r") as f :
                done = f.read().split("\n")
                if "" in done : done.remove("")

            for slug in scan_VE() :
                if not slug in pendiente :
                    pendiente.append(slug)

            for slug in pendiente :
                T = get_by_slug(slug)
                if "errors" in T :
                    printl(T["errors"])
                    continue
                if T["data"]["tournament"] :
                    torneos.append(T["data"]["tournament"])

            for torneo in torneos :
                print(torneo)
                for r in resultados(torneo) :
                    printl(r)
                    try :
                        twitter_api.PostUpdate(r)
                        pass
                    except Exception as e :
                        printl("peo de twitter, longitud:",len(r))
                        printl(e)

            with open("pendiente.txt","w") as f :
                f.truncate()
                f.write("\n".join(pendiente))

            with open("done_events.txt","w") as f :
                f.truncate()
                f.write("\n".join(done))

            pendiente = []
            torneos = []
            done = []
            T = {}
            printl("voy a dormir 10 minuticos")
            time.sleep(600)
        except Exception as e :
            printl(e)
            time.sleep(600)
