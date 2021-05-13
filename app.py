#!/usr/bin/env python3
import subprocess
import sys
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit

sys.path.append("./refresh_extract")

from refresh_extract import main

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret!"
app.config["cmd"] = "python ./refresh_extract/main.py -c ./config/config-km.yaml -q 'movies'"
socketio = SocketIO(app,
                    cors_allowed_origins='*',
                    ping_timeout=60000)


# log = logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/runAction', methods=['POST'])
def runAction():
    request_data = request.get_json()
    main.embedded_start(request_data["query"], socketio)
    resp = jsonify(success=True)
    return resp


@app.route('/incoming', methods=['POST'])
def incoming():
    print('INCOMING EVENT')
    request_data = request.get_json()
    event = request_data['event_type']
    resource = request_data['resource_name']
    print(event + resource)
    socketio.emit('push-message', f'Webhook Event -> {event} | Resource "{resource}"', broadcast=True)
    resp = jsonify(success=True)
    return resp

@socketio.on('connect')
def handle_message():
    print('CONNECT EVENT')

@socketio.on('disconnect')
def handle_message():
    print('DISCONNECT EVENT')

def run_script_using_subprocess(data):
    result = subprocess.call(
        [sys.executable,
         "./refresh_extract/main.py",
            "-c", "./config/config-km.yaml",
            "-q", "movies"
         ])


if __name__ == '__main__':
    socketio.run(app)
