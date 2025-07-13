import os
from api import create_app
from chatbot.socket import socketio
import chatbot.chatlogic.chat


application = create_app()
socketio.init_app(application)
FLASK_PORT = int(os.getenv("FLASK_PORT", 8000))


if __name__ == "__main__":
    socketio.run(app=application, host="0.0.0.0", port=FLASK_PORT, debug=True)
