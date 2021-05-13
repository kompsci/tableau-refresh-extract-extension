#!/usr/bin/env python3
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret!"
socketio = SocketIO(app, cors_allowed_origins='*')


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/incoming', methods=['POST'])
def incoming():
    event = request.form['event_type']
    resource = request.form['resource_name']
    print(event + resource)
    socketio.emit('push-message', {'data': f'Webhook Event -> {event} | Resource "{resource}"'}, broadcast=True)
    resp = jsonify(success=True)
    return resp

@socketio.on('connect')
def handle_message():
    print('CONNECT EVENT')

@socketio.on('disconnect')
def handle_message():
    print('DISCONNECT EVENT')

@socketio.on('client-event')
def handle_my_custom_event(data):
    print('Received Message: ' + str(data))



if __name__ == '__main__':
    socketio.run(app)
