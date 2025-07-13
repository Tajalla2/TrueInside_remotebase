from flask import request
from flask_socketio import SocketIO, join_room, leave_room


socketio = SocketIO(async_mode="gevent")


@socketio.on("connect")
def handle_connect():
    sid = request.sid
    join_room(sid)
    print("client connected server side")


@socketio.on("disconnect")
def handle_disconnect():
    sid = request.sid
    leave_room(sid)
    print("client disconnected")
