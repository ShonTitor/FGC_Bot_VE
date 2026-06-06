import asyncio
import time
import traceback
import sys
from database import *
from apis import *
from datetime import datetime
from barkr.connections import ConnectionMode, TelegramConnection, TwitterConnection
from barkr.models import Message
from PIL import Image

path = os.path.realpath(__file__)
path = os.path.abspath(os.path.join(path, os.pardir))
with open(os.path.join(path, "config.json"), "r") as f:
    config = json.loads(f.read())

debug = config.get("debug", False)

db_file = config["db_file"] if not debug else config["debug_db_file"]

_connections = []
if config.get("twitter_enabled"):
    _connections.append(TwitterConnection(
        "Twitter",
        [ConnectionMode.WRITE],
        config["twitter_consumer_key"],
        config["twitter_consumer_secret"],
        config["twitter_access_token_key"],
        config["twitter_access_token_secret"],
        config["twitter_bearer_token"],
    ))
if config.get("telegram_enabled"):
    _connections.append(TelegramConnection(
        "Telegram",
        [ConnectionMode.WRITE],
        config["telegram_token"],
        config["telegram_chat_id"],
    ))

def post_tweet(text, img=None):
    for conn in _connections:
        if img is not None and isinstance(conn, TelegramConnection):
            asyncio.run(conn.app.bot.send_photo(
                chat_id=conn.chat_id,
                photo=io.BytesIO(base64.b64decode(img)),
                caption=text,
            ))
        else:
            conn._post([Message(id="0", message=text, source_connection="FGC Bot VE", media=[])])

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
            page_events = sgg_data["events"]
            tournaments = sgg_data["tournaments"]
            newfound = []
            for ev in page_events:
                slug = ev["slug"]
                sgg_id = ev["id"]
                existing = get_event_by_sgg_id(conn, sgg_id)
                if existing is None:
                    if not event_exists(conn, slug):
                        insert_events(conn, [(slug, sgg_id)])
                        newfound.append(slug)
                elif existing[0] != slug:
                    printl(f"Slug changed for event {sgg_id}: {existing[0]} -> {slug}")
                    update_event_slug(conn, sgg_id, slug)
            if len(newfound) > 0 :
                printl("Found new events: \n"+" \n".join(newfound))
            time.sleep(1)

            for tournament in tournaments:
                if all(event["slug"] in newfound for event in tournament["events"]):
                    new_tournaments.append(tournament)

            if not page_events :
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
                post_tweet(announcement_text)
                time.sleep(60)
        except Exception:
            printl(traceback.format_exc())

    try:
        printl("Checking if any pending events are complete")
        pending = pending_events(conn)
        thirty_days_ago = time.time() - 30 * 24 * 3600
        for slug in pending :
            try:
                printl(f"Checking if {slug} is complete")
                checked = check_event(slug)
                time.sleep(1)
                if checked is None :
                    printl(f"Event {slug} not found (404), removing from DB")
                    delete_event(conn, slug)
                    continue
                is_complete, start_at = checked
                if not is_complete and start_at > 0 and start_at < thirty_days_ago:
                    printl(f"Event {slug} started over 30 days ago and is not complete, removing from DB")
                    delete_event(conn, slug)
                    continue
                if is_complete :
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
                            printl("Getting top 8 graphic from Top8er API")
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
                            printl(f"Error getting top 8 graphic for {slug}")
                            printl(traceback.format_exc())
                            img = None
                            
                    else:
                        printl("Skipping top 8 graphic")
                        img = None

                    result_text = format_data(data)
                    try:
                        if not debug:
                            post_tweet(result_text, img)
                        complete_event(conn, slug)
                        if not debug:
                            time.sleep(60)
                    except Exception:
                        printl(traceback.format_exc())

                    printl(result_text + "\n\n\n")
                time.sleep(1)
            except Exception:
                printl(traceback.format_exc())

    except Exception:
        printl(traceback.format_exc())

    printl("sleeping")
    time.sleep(300)

