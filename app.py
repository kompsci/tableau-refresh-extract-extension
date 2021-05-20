#!/usr/bin/env python3
import subprocess
import sys
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit

sys.path.append("./refresh_extract")

from refresh_extract import main

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret!"
socketio = SocketIO(app,
                    cors_allowed_origins='*',
                    ping_timeout=60000)


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
    event_type = request_data['event_type']
    resource_name = request_data['resource_name']
    print(f'INCOMING: {event_type} | {resource_name}')
    if (event_type == 'DatasourceCreated' and resource_name == 'GooglePlacesData'):
        socketio.emit('refresh-data', f'Webhook {event_type} received <br/>Resource "{resource_name}"', broadcast=True)
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


# if __name__ == '__main__':
#     socketio.run(app)
