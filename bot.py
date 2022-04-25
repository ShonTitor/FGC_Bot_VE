import re
import time
import traceback
from database import *
from apis import *
from datetime import datetime
import twitter

path = os.path.realpath(__file__)
path = os.path.abspath(os.path.join(path, os.pardir))
with open(os.path.join(path, "config.json"), "r") as f:
    config = json.loads(f.read())
    db_file = config["db_file"]

# Cosas de twitter
twitter_api = twitter.Twitter(auth=twitter.OAuth(
                                config["twitter_access_token_key"],
                                config["twitter_access_token_secret"],
                                config["twitter_consumer_key"],
                                config["twitter_consumer_secret"]))

db_path = os.path.join(path, db_file)
conn = create_connection(db_path)

def printl(s):
    now = datetime.now()
    s = now.strftime("%d/%m/%Y %H:%M:%S") + " " + s
    print(s)
    with open(os.path.join(path, "log.txt"), "a") as f:
        f.write(s + "\n")

while True :
    try:
        # Check for new pending tournaments
        printl("Looking for new pending tournaments")
        page = 1
        while True:
            slugs = scan_sgg(page=page)
            newfound = []
            for slug in slugs :
                if not event_exists(conn, slug):
                    insert_events(conn, [slug])
                    newfound.append(slug)
            if len(newfound) > 0 :
                printl("Found new events: \n"+" \n".join(newfound))
            time.sleep(1)
            if slugs == [] :
                break
            page += 1
    except Exception:
        printl(traceback.format_exc())

    try:
        printl("Checking if any pending events are complete")
        pending = pending_events(conn)
        for slug in pending :
            try:
                printl(f"Checking if {slug} is complete")
                checked = check_event(slug)
                if checked is None :
                    printl("Couldn't find event "+slug)
                    continue
                if checked :
                    data = event_data(slug)

                    if data["game"] in ["ssbu", "melee"] \
                       and len(data["players"]) >= 8 \
                       and not all(p["char"][0] == "Random" for p in data["players"]\
                           ):

                        top8er = get_top8er(data)
                        if "error" in top8er:
                            printl(f"top8er API error: {top8er['error']}")
                            img = None
                        else:
                            #base64_img = base64.b64decode(top8er["base64_img"])
                            #buffer = io.BytesIO(base64_img)
                            #img = Image.open(buffer)
                            #img.save("result.png")
                            img = top8er["base64_img"]
                    else:
                        printl(f"Skipping top 8 graphic for game: {data['game']}")
                        img = None

                    result_text = format_data(data)
                    try:
                        if img:
                            params = {"status": result_text, "media[]": img, "_base64": True}
                            twitter_api.statuses.update_with_media(**params)
                        else:
                            twitter_api.statuses.update(status=result_text)
                    except Exception:
                        printl(traceback.format_exc())

                    complete_event(conn, slug)

                    printl(result_text + "\n\n\n")
                    time.sleep(1)
            except Exception:
                printl(traceback.format_exc())

    except Exception:
        printl(traceback.format_exc())

    printl("sleeping")
    time.sleep(60)

