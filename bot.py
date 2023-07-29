import time
import traceback
import sys
from database import *
from apis import *
from datetime import datetime
import twitter
from PIL import Image

path = os.path.realpath(__file__)
path = os.path.abspath(os.path.join(path, os.pardir))
with open(os.path.join(path, "config.json"), "r") as f:
    config = json.loads(f.read())

debug = config.get("debug", False)

db_file = config["db_file"] if not debug else config["debug_db_file"]

# Cosas de twitter
twitter_api = twitter.Twitter(auth=twitter.OAuth(
                                config["twitter_access_token_key"],
                                config["twitter_access_token_secret"],
                                config["twitter_consumer_key"],
                                config["twitter_consumer_secret"]))

arrecho = False
if "--arrecho" in sys.argv:
    print("MODO ARRECHO ACTIVADO")
    #set_all_pending(conn)
    if os.path.exists(db_file):
        os.remove(db_file)
    arrecho = True

db_path = os.path.join(path, db_file)
conn = create_connection(db_path)

def printl(s):
    now = datetime.now()
    s = now.strftime("%d/%m/%Y %H:%M:%S") + " " + s
    print(s)
    #with open(os.path.join(path, "log.txt"), "a") as f:
    #    f.write(s + "\n")

while True :

    new_tournaments = []
    try:
        # Check for new pending tournaments
        printl("Looking for new pending tournaments")
        page = 1
        while True:
            sgg_data = scan_sgg(page=page, modo_arrecho=arrecho)
            if sgg_data is None:
                printl("Error in start gg query")
                continue
            slugs = sgg_data["events"]
            tournaments = sgg_data["tournaments"]
            newfound = []
            for slug in slugs :
                if not event_exists(conn, slug):
                    insert_events(conn, [slug])
                    newfound.append(slug)
            if len(newfound) > 0 :
                printl("Found new events: \n"+" \n".join(newfound))
            time.sleep(1)

            for tournament in tournaments:
                if any(event["slug"] in newfound for event in tournament["events"]):
                    new_tournaments.append(tournament)
            
            if slugs == [] :
                break
            page += 1
    except Exception:
        printl(traceback.format_exc())

    for tournament in new_tournaments:
        try:
            tournament.pop("events")
            announcement_text = [
                "Nuevo torneo encontrado:\n",
                f"{tournament['name']}\n",
                f"Ciudad: {tournament['city']}\n",
                f"https://www.start.gg/{tournament['shortSlug'] or tournament['slug']}"
            ]
            announcement_text = "\n".join(announcement_text)
            print(tournament)
            printl(announcement_text)

            if not debug:
                twitter_api.statuses.update(status=announcement_text)
                time.sleep(30)
        except Exception:
            printl(traceback.format_exc())

    try:
        printl("Checking if any pending events are complete")
        pending = pending_events(conn)
        for slug in pending :
            try:
                printl(f"Checking if {slug} is complete")
                checked = check_event(slug)
                time.sleep(1)
                if checked is None :
                    printl("Couldn't find event "+slug)
                    #complete_event(conn, slug)
                    continue
                if checked :
                    data = event_data(slug)
                    time.sleep(1)

                    #print(data["players"])

                    if len(data["players"]) == 0:
                        printl(f"Skipping {slug} because it has 0 players")
                        continue

                    if data["players"][0]["position"] == 2:
                        printl(f"Skipping {slug} because it has 2 second places")
                        continue

                    if "game" in data and data.get("gameId") in config["top8er_gameIds"] \
                       and len(data["players"]) >= 8 \
                       and not all(p["char"] is None or p["char"][0] == "Random" for p in data["players"]\
                           ):

                        try:
                            top8er = get_top8er_new(data)
                            if top8er is None:
                                img = None
                            else:
                                img = top8er["base64_img"]
                            if debug:
                                base64_img = base64.b64decode(top8er["base64_img"])
                                buffer = io.BytesIO(base64_img)
                                debug_img = Image.open(buffer)
                                debug_img.save(os.path.join("debug_images", f"{slug.replace('/', '_')}.png"), optimize=True)
                        except Exception:
                            printl(traceback.format_exc())
                            img = None
                            
                    else:
                        printl("Skipping top 8 graphic")
                        img = None

                    result_text = format_data(data)
                    try:
                        if not debug:
                            if img:
                                params = {"status": result_text, "media[]": img, "_base64": True}
                                twitter_api.statuses.update_with_media(**params)
                            else:
                                twitter_api.statuses.update(status=result_text)
                            time.sleep(30)
                        complete_event(conn, slug)
                    except Exception:
                        printl(traceback.format_exc())

                    printl(result_text + "\n\n\n")
                time.sleep(1)
            except Exception:
                printl(traceback.format_exc())

    except Exception:
        printl(traceback.format_exc())

    printl("sleeping")
    time.sleep(60)

