#!/usr/bin/env python3
from flask import Flask, render_template
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

@app.route('/incoming')
def incoming(msg):
    pass


@socketio.on('connect')
def handle_message():
    print('connected')

@socketio.on('client event')
def handle_my_custom_event(json):
    print('received json: ' + str(json))
    emit('server data', {'data': 'Message From Server'})
    emit('server data', {'data': 'Message From Server 2'})



if __name__ == '__main__':
    socketio.run(app)
