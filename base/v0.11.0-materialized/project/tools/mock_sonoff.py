#!/usr/bin/env python3
"""Tiny SONOFF DIY-like HTTP mock for development on a LAN. Not used by the Android app."""
from http.server import BaseHTTPRequestHandler, HTTPServer
import json, threading, time

STATE = {"switch":"off", "startup":"off", "pulse":"off", "pulseWidth":500}

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_POST(self):
        n=int(self.headers.get('content-length','0'))
        body=json.loads(self.rfile.read(n) or b'{}')
        data=body.get('data',{})
        if self.path.endswith('/pulse'):
            STATE['pulse']=data.get('pulse', STATE['pulse'])
            if 'pulseWidth' in data: STATE['pulseWidth']=data['pulseWidth']
        elif self.path.endswith('/switch'):
            STATE['switch']=data.get('switch', STATE['switch'])
            if STATE['switch']=='on' and STATE['pulse']=='on':
                ms=STATE['pulseWidth']
                threading.Thread(target=lambda:(time.sleep(ms/1000), STATE.__setitem__('switch','off')),daemon=True).start()
        out=json.dumps({"seq":1,"error":0,"data":STATE if self.path.endswith('/info') else {}}).encode()
        self.send_response(200); self.send_header('content-type','application/json'); self.send_header('content-length',str(len(out))); self.end_headers(); self.wfile.write(out)

print('Mock SONOFF on http://0.0.0.0:8081')
HTTPServer(('0.0.0.0',8081),H).serve_forever()
