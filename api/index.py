from http.server import BaseHTTPRequestHandler
import subprocess

class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()

        self.wfile.write(
            b'Streamlit app should be deployed using Streamlit Cloud or Render instead of Vercel.'
        )