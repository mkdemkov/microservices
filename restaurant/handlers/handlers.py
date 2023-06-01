from flask import Blueprint, request, Response, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
import os
from dotenv import load_dotenv
from entities.entities import User, Order, Dish
from restaurant.database.connect import get_session
import hashlib
import jwt

app_handlers = Blueprint('handlers', __name__)
load_dotenv()
engine = create_engine(os.getenv('path_to_database'))
Session = sessionmaker(bind=engine)
session = Session()


@app_handlers.route('/new', methods=['POST'])
def create_order():
    data = request.get_json()

    if 'user_id' not in data or 'dishes' not in data:
        return jsonify({'message': 'Пожалуйста, заполните все обязательные поля'}), 400

    user_id = data.get('user_id')
    status = data.get('status', 'в работе')
    special_requests = data.get('special_requests')
    dishes = data.get('dishes')

    session = get_session()

    users = session.query(User).all()
    user_exists = any(user.id == user_id for user in users)

    if not user_exists:
        return jsonify({'message': 'Пользователя с таким id не существует'}), 400

    for dish_id in dishes:
        dish = session.query(Dish).filter_by(id=dish_id).first()
        if not dish:
            return jsonify({'message': f'Блюда с id = {dish_id} не существует'}), 400

    order = Order(user_id=user_id, status=status, special_requests=special_requests, dishes=dishes)
    session.add(order)
    session.commit()

    return jsonify({'message': 'Заказ успешно добавлен'}), 201


