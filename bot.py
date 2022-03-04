import re
import time
import traceback
from database import *
from apis import *
from datetime import datetime

with open(os.path.join(path, "config.json"), "r") as f:
    config = json.loads(f.read())
    db_file = config["db_file"]

conn = create_connection(db_file)

def printl(s):
    now = datetime.now()
    s = now.strftime("%d/%m/%Y %H:%M:%S") + " " + s
    print(s)
    with open("log.txt", "a") as f:
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
            checked = check_event(slug)
            if checked is None :
                printl("Couldn't find event "+slug)
                continue
            if checked :
                data = event_data(slug)
                
                if data["game"] in ["ssbu", "melee"] \
                   and len(data["players"]) >= 8 \
                   and not all(p["char"][0] == "Random" for p in data["players"]):
                    top8er = get_top8er(data)
                    if "error" in top8er:
                        printl(f"top8er API error: {top8er['error']}")
                        img = None
                    else:
                        base64_img = base64.b64decode(top8er["base64_img"])
                        buffer = io.BytesIO(base64_img)
                        img = Image.open(buffer)
                        img.save("result.png")
                else:
                    printl(f"Skipping top 8 graphic for game: {data['game']}")
                    img = None

                if img:
                    img.show()
                    input()
                        
                result_text = format_data(data)
                complete_event(conn, slug)
                    
                printl(result_text + "\n\n\n")
    except Exception:
        printl(traceback.format_exc())

    printl("sleeping")
    time.sleep(5)

