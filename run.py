from app import create_app, socketio
from app.config import Config
import subprocess

app = create_app(Config)
print(app.config["MONGO_URI"])  # Untuk mengecek apakah URI terkonfigurasi dengan benar


if __name__ == "__main__":
    # subprocess.Popen(["streamlit", "run", "streamlit.py"])
    socketio.run(app, host="0.0.0.0", port=6000, debug=True, allow_unsafe_werkzeug=True)
