import re
import time
from database import *
from apis import *

with open(os.path.join(path, "config.json"), "r") as f:
    config = json.loads(f.read())
    db_file = config["db_file"]

conn = create_connection(db_file)

h = """
pending: see the list of pending tournaments
add <https://smash.gg/tournament/.../event/...>: add smash.gg event
add <https://challonge.com/...>: add challonge event
scan: checks for new tournaments on smash.gg
check: checks if any pending tournaments are over
help: print this help info
exit: close the application
"""
print(h)

while True :
    message = input("\nEnter a command: ")

    if message.startswith('pending') :
        slugs = pending_events(conn)
        print(" \n".join(slugs))

    elif message.startswith('add') :
        # parsing
        match = re.search('tournament/[^/]+/event/[^/]+', message)
        if match is None :
            match = re.search("https://challonge.com/[^/]+", message)
            site = "challonge"
            if match is not None :
                slug = match[0][22:]
            else :
                match = re.search("[^\./]+.challonge.com/[^/]+", message)
                if match is None :
                    print("Couldn't parse url")
                    continue
                else :
                    s = match[0].split(".")
                    s1 = s[0]
                    s2 = s[2][4:]
                    slug = s1+"-"+s2
        else :
            slug = match[0]
            site = "smash.gg"

        checked = check_event(slug)

        if checked is None :
            print("Couldn't find event")
            continue
        if not event_exists(conn, slug):
            insert_events(conn, [slug])
            print("Event saved")
    
    elif message.startswith('scan') :
        page = 1
        while True:
            slugs = scan_sgg(page=page)
            newfound = []
            for slug in slugs :
                if not event_exists(conn, slug):
                    insert_events(conn, [slug])
                    newfound.append(slug)
            if len(newfound) > 0 :
                print("Found new events: \n"+" \n".join(newfound))
            if slugs == [] :
                break
            page += 1

    elif message.startswith('check') :
        print("Checking if any pending events are complete")
        pending = pending_events(conn)
        for slug in pending :
            checked = check_event(slug)
            if checked is None :
                print("Couldn't find event "+slug)
                continue
            if checked :
                result = format_data(event_data(slug))
                complete_event(conn, slug)
                with open("results.txt", "a", encoding='utf-8') as f :
                    f.write(result+"\n\n\n")
                print(result+"\n\n\n")

    elif message.startswith('help') :
        print(h)

    elif message.startswith('exit') :
        break
