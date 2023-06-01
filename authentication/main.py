import os
from dotenv import load_dotenv
from flask import Flask

from handlers.handlers import app_handlers

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('secret_key')  # Секретный ключ для генерации токена
app.register_blueprint(app_handlers)

if __name__ == '__main__':
    app.run(debug=True, port=8080)
