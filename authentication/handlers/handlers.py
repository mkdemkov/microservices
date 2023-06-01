from flask import Blueprint, request, Response, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
import os
from dotenv import load_dotenv
from entities.entities import User
from authentication.database.connect import get_session
import hashlib
import jwt

app_handlers = Blueprint('handlers', __name__)
load_dotenv()
engine = create_engine(os.getenv('path_to_database'))
Session = sessionmaker(bind=engine)
session = Session()


@app_handlers.route('/register', methods=['POST'])
def register():
    from authentication.main import app
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'customer')

    if not username or not email or not password:
        return jsonify({'message': 'Пожалуйста, заполните все обязательные поля'}), 400

    if '@' not in email:
        return jsonify({'message': 'Некорректный адрес электронной почты'}), 400

    if len(password) < 6:
        return jsonify({'message': 'Длина пароля должна быть не менее 6 символов'}), 400

    user = session.query(User).filter((User.username == username) | (User.email == email)).first()
    if user:
        return jsonify(
            {'message': 'Пользователь с таким именем пользователя или адресом электронной почты уже существует'}), 409
    password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
    new_user = User(username=username, email=email, password_hash=password_hash, role=role)
    session.add(new_user)
    session.commit()

    # token = jwt.encode({'username': username, 'role': role}, app.config['SECRET_KEY'], algorithm='HS256')

    # Возврат успешного ответа с токеном
    return jsonify({'message': 'Пользователь успешно зарегистрирован'}), 201


@app_handlers.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'message': 'Пожалуйста, введите адрес электронной почты и пароль'}), 400

    session = get_session()  # Получение сессии базы данных

    user = session.query(User).filter_by(email=email).first()

    entered_password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()

    if not user or entered_password_hash != user.password_hash:
        session.close()
        return jsonify({'message': 'Неверное имя пользователя или пароль'}), 401

    token = jwt.encode({'user_id': user.id, 'email': user.email}, os.getenv('secret_key'), algorithm='HS256')

    session.close()  # Закрываем сессию базы данных

    return jsonify({'message': 'Успешный вход в систему', 'token': token}), 200


@app_handlers.route("/user", methods=['GET'])
def get_user_info():
    from authentication.main import app
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': 'Токен отсутствует'}), 401

    try:
        # Декодируем токен
        decoded_token = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        user_id = decoded_token.get('user_id')
        email = decoded_token.get('email')

        session = get_session()

        user = session.query(User).filter_by(email=email).first()

        role = user.role

        # Возвращаем информацию о пользователе
        return jsonify({'user_id': user_id, 'email': email, 'role' : role}), 200

    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Истек срок действия токена'}), 401

    except jwt.InvalidTokenError:
        return jsonify({'message': 'Неверный токен'}), 401
