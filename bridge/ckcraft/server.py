"""Authenticated loopback API. No CORS, game/control data in URLs or secrets in logs."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hmac
import json
import re

from .state import Conflict

IDENTIFIER = re.compile(r"^[A-Za-z0-9-]{1,64}$")


def make_server(state, token: str, port: int = 0):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *args):
            pass

        def reply(self, code, data):
            body = json.dumps(data,ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header("Content-Type","application/json; charset=utf-8")
            self.send_header("Content-Length",str(len(body)))
            self.send_header("Cache-Control","no-store")
            self.send_header("Connection","close")
            self.end_headers()
            self.wfile.write(body)
            self.close_connection = True

        def authenticated(self):
            if self.headers.get("Origin") is not None:
                self.reply(403,{"error":"browser origins are not permitted"})
                return False
            host = self.headers.get("Host","")
            if host not in {f"127.0.0.1:{self.server.server_port}",f"localhost:{self.server.server_port}"}:
                self.reply(403,{"error":"invalid loopback host"})
                return False
            if not hmac.compare_digest(self.headers.get("Authorization","").encode("utf-8"),("Bearer "+token).encode("utf-8")):
                self.reply(401,{"error":"authentication required"})
                return False
            return True

        def do_GET(self):
            if not self.authenticated():
                return
            if self.path == "/v1/session":
                self.reply(200,state.snapshot())
            elif self.path == "/v1/health":
                self.reply(200,{"protocol":1,"status":"running","gameplayVerified":False})
            else:
                self.reply(404,{"error":"unknown endpoint"})

        def do_POST(self):
            if not self.authenticated():
                return
            try:
                if self.headers.get("Transfer-Encoding"):
                    raise ValueError("chunked bodies are not accepted")
                length = int(self.headers.get("Content-Length","0"))
                if not 1 <= length <= 4096:
                    raise ValueError("invalid body size")
                if self.headers.get_content_type() != "application/json":
                    raise ValueError("expected application/json")
                data = json.loads(self.rfile.read(length))
                keys = {"session","player","instance"} | ({"outcome"} if self.path == "/v1/result" else set())
                if not isinstance(data,dict) or set(data) != keys:
                    raise ValueError("unexpected request fields")
                if any(not isinstance(data[k],str) or not IDENTIFIER.fullmatch(data[k]) for k in keys):
                    raise ValueError("invalid identifier")
                if self.path == "/v1/claim":
                    result = state.claim(data["session"],data["player"],data["instance"])
                elif self.path == "/v1/result":
                    result = state.result(data["session"],data["player"],data["instance"],data["outcome"])
                else:
                    self.reply(404,{"error":"unknown endpoint"})
                    return
                self.reply(200,result)
            except Conflict as error:
                self.reply(409,{"error":str(error)})
            except (ValueError,TypeError,UnicodeError) as error:
                self.reply(400,{"error":str(error)})

    class Server(ThreadingHTTPServer):
        daemon_threads = True

        def get_request(self):
            sock, address = super().get_request()
            sock.settimeout(5)
            return sock,address

    return Server(("127.0.0.1",port),Handler)
