from functools import wraps

from flask import Blueprint, request, Response, jsonify, abort
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
        dish.quantity -= 1
        session.commit()

    order = Order(user_id=user_id, status=status, special_requests=special_requests, dishes=dishes)
    session.add(order)
    session.commit()

    return jsonify({'message': 'Заказ успешно добавлен'}), 201


@app_handlers.route('/orders', methods=['GET'])
def get_order():
    order_id = request.args.get('order_id')
    if not order_id:
        return jsonify({'Ошибка': 'Не указан id заказа в параметрах запроса'}), 401
    session = get_session()

    try:
        # Получение заказа по идентификатору
        order = session.query(Order).get(order_id)

        if order:
            response = {
                'id': order.id,
                'status': order.status
            }
            return jsonify(response), 200
        else:
            # Обработка случая, когда заказ не найден
            return jsonify({'Ошибка': 'Заказ не найден'}), 404

    except Exception as e:
        return jsonify({'Ошибка': str(e)}), 500

    finally:
        session.close()


def manager_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Проверка роли пользователя
        user_id = request.headers.get('User-Id')
        session = Session()
        user = session.query(User).filter_by(id=user_id).first()
        session.close()

        if user and user.role == 'manager':
            return f(*args, **kwargs)
        else:
            abort(401, 'Unauthorized')

    return decorated


@app_handlers.route('/dishes', methods=['GET'])
@manager_required
def get_dishes():
    # Открытие сессии SQLAlchemy
    session = Session()

    try:
        # Получение всех блюд
        dishes = session.query(Dish).all()

        # Формирование списка блюд в формате JSON
        response = [{'id': dish.id, 'name': dish.name, 'description': dish.description, 'price': dish.price,
                     'quantity': dish.quantity} for dish in dishes]
        return jsonify(response), 200

    except Exception as e:
        # Обработка исключений
        return jsonify({'error': str(e)}), 500

    finally:
        # Закрытие сессии SQLAlchemy
        session.close()


@app_handlers.route('/dish', methods=['GET'])
@manager_required
def get_dish():
    dish_id = request.args.get('dish_id')
    if not dish_id:
        return jsonify({'Ошибка': 'Id блюда не задан'}), 401
    session = Session()

    try:
        # Получение блюда по идентификатору
        dish = session.query(Dish).get(dish_id)

        if dish:
            # Формирование ответа JSON с информацией о блюде
            response = {'id': dish.id, 'name': dish.name, 'description': dish.description, 'price': dish.price,
                        'quantity': dish.quantity}
            return jsonify(response), 200
        else:
            # Обработка случая, когда блюдо не найдено
            return jsonify({'Ошибка': 'Блюдо не найдено'}), 404

    except Exception as e:
        # Обработка исключений
        return jsonify({'error': str(e)}), 500

    finally:
        session.close()


@app_handlers.route('/dishes', methods=['POST'])
@manager_required
def create_dish():
    # Открытие сессии SQLAlchemy
    session = Session()

    try:
        # Получение данных блюда из запроса
        data = request.json

        if not 'name' in data or not 'price' in data or not 'quantity' in data:
            return jsonify({'Ошибка': 'Заполните все необходимые поля'}), 401

        if not 'description' in data:
            data['description'] = ''

        # Создание нового блюда
        dish = Dish(name=data['name'], description=data['description'], price=data['price'], quantity=data['quantity'])

        # Добавление блюда в базу данных
        session.add(dish)
        session.commit()

        # Формирование ответа JSON с информацией о созданном блюде
        return jsonify({'message': 'Блюдо успешно добавлено!'}), 201

    except Exception as e:
        # Обработка исключений
        session.rollback()
        return jsonify({'error': str(e)}), 500

    finally:
        # Закрытие сессии SQLAlchemy
        session.close()


@app_handlers.route('/dishes/<int:dish_id>', methods=['PUT'])
@manager_required
def update_dish(dish_id):
    # Открытие сессии SQLAlchemy
    session = Session()

    try:
        # Получение данных блюда из запроса
        data = request.json

        # Получение блюда по идентификатору
        dish = session.query(Dish).get(dish_id)

        if dish:
            # Обновление данных блюда
            dish.name = data['name'] if 'name' in data else dish.name
            dish.description = data['description'] if 'description' in data else dish.description
            dish.price = data['price'] if 'price' in data else dish.price
            dish.quantity = data['quantity'] if 'quantity' in data else dish.quantity

            session.commit()

            # Формирование ответа JSON с информацией об обновленном блюде
            return jsonify({'message': 'Блюдо успешно обновлено!'}), 201
        else:
            # Обработка случая, когда блюдо не найдено
            return jsonify({'Ошибка': 'Блюдо не найдено'}), 404

    except Exception as e:
        # Обработка исключений
        session.rollback()
        return jsonify({'error': str(e)}), 500

    finally:
        # Закрытие сессии SQLAlchemy
        session.close()
