import socket
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'OK')

    def log_message(self, format, *args):
        return

def start_http():
    server = HTTPServer(('0.0.0.0', 5555), SimpleHandler)
    print('HTTP mock running on 5555')
    server.serve_forever()

def handle_redis_client(conn, addr):
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            # very naive: respond to PING with +PONG\r\n
            if b'PING' in data.upper() or data.startswith(b'*1'):
                conn.sendall(b'+PONG\r\n')
            else:
                # default PONG
                conn.sendall(b'+OK\r\n')
    finally:
        conn.close()

def start_redis():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('0.0.0.0', 6379))
    s.listen(5)
    print('Mock Redis listening on 6379')
    try:
        while True:
            conn, addr = s.accept()
            t = threading.Thread(target=handle_redis_client, args=(conn, addr), daemon=True)
            t.start()
    finally:
        s.close()

if __name__ == '__main__':
    t1 = threading.Thread(target=start_http, daemon=True)
    t1.start()
    start_redis()
