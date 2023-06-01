from flask import Blueprint, request, Response, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
import os
from dotenv import load_dotenv
from authentication.database.entities.user import User
import bcrypt
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
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    new_user = User(username=username, email=email, password_hash=password_hash, role=role)
    session.add(new_user)
    session.commit()

    # token = jwt.encode({'username': username, 'role': role}, app.config['SECRET_KEY'], algorithm='HS256')

    # Возврат успешного ответа с токеном
    return jsonify({'message': 'Пользователь успешно зарегистрирован'}), 201



