from pathlib import Path
import argparse
import json
import logging
import os
import secrets
import threading
import time

from .log_reader import LogReader
from .protocol import parse_line, Request, Ack
from .server import make_server
from .state import State, Conflict


def main():
    parser = argparse.ArgumentParser(description="CKCraft development bridge (not a verified Melty release)")
    parser.add_argument("--ck3-log",type=Path,required=True,help="Player's Documents/Paradox Interactive/Crusader Kings III/logs/debug.log")
    parser.add_argument("--state",type=Path,required=True,help="Private state directory dedicated to one disposable campaign")
    parser.add_argument("--campaign",required=True,help="Stable label for this campaign; do not share state between campaigns")
    parser.add_argument("--port",type=int,default=0)
    parser.add_argument("--design",type=Path,default=Path(__file__).resolve().parents[2]/"design"/"sheets")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO,format="%(levelname)s %(message)s")
    state = State(args.state,args.campaign,args.design)
    token = secrets.token_urlsafe(32)
    server = make_server(state,token,args.port)
    config = args.state/"bridge.json"
    temp = config.with_suffix(".tmp")
    temp.write_text(json.dumps({"protocol":1,"host":"127.0.0.1","port":server.server_port,"token":token}),encoding="utf-8")
    if os.name != "nt":
        temp.chmod(0o600)
    temp.replace(config)
    tail = LogReader(args.ck3_log)
    tail.read() # Establish EOF before the CK3 event, including after bridge restarts.
    threading.Thread(target=server.serve_forever,daemon=True).start()
    logging.info("Bridge running. Private client configuration: %s",config)
    logging.info("Results remain pending until CK3 logs the matching ACK. No console automation is enabled.")
    try:
        while True:
            try:
                for line in tail.read():
                    try:
                        frame = parse_line(line)
                        if isinstance(frame,Request):
                            if state.accept(frame):
                                logging.info("CK3 event accepted: %s",frame.scenario)
                        elif isinstance(frame,Ack) and state.acknowledge(frame):
                            logging.info("CK3 acknowledged the result.")
                    except (ValueError,Conflict) as error:
                        logging.warning("Frame rejected: %s",error)
            except ValueError as error:
                logging.warning("Log reader: %s",error)
            time.sleep(0.25)
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        server.server_close()
        state.close()
        config.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
