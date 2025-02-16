from flask import Blueprint
from app import socketio
from app.services.socketio_services import handle_connect, handle_disconnected, handle_image, handle_message

bp = Blueprint('socketio', __name__)

@socketio.on('connect')
def on_connect():
    handle_connect()
    
@socketio.on('disconnect')
def on_disconnected():
    handle_disconnected()
    
@socketio.on('message')
def on_message(message):
    handle_message(message)

@socketio.on('image')
def on_image(data):
    handle_image(data)
