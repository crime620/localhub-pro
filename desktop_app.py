import threading
import webview
from app import app

def run_flask():
    app.run(debug=False, host="127.0.0.1", port=5000)

threading.Thread(target=run_flask).start()

webview.create_window("LocalHub Pro", "http://127.0.0.1:5000", width=1400, height=900)
webview.start()