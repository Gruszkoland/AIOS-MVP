"""
Harmonia 369 Dashboard Server
Serwer HTTP hostujący dashboard Licznika Harmonii.
Port: 3690 (3-6-9-0)
"""
import http.server
import os

PORT = 3690
DIRECTORY = os.path.dirname(os.path.abspath(__file__))


class HarmoniaHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()


if __name__ == '__main__':
    with http.server.HTTPServer(('', PORT), HarmoniaHandler) as httpd:
        print(f'[Harmonia 369] Dashboard aktywny: http://localhost:{PORT}')
        print(f'[Harmonia 369] Katalog: {DIRECTORY}')
        print(f'[Harmonia 369] Ctrl+C aby zatrzymać')
        httpd.serve_forever()
