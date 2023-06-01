import os
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv
from entities.entities import Order

def start_order_processing():
    global session
    try:
        # Создание подключения к базе данных с использованием SQLAlchemy
        load_dotenv()
        engine = create_engine(os.getenv('path_to_database'))
        Session = sessionmaker(bind=engine)
        session = Session()

        # Запуск внутреннего обработчика заказов
        while True:
            # Получение заказов в статусе "в ожидании"
            orders = session.query(Order).filter(Order.status == 'в работе').all()

            for order in orders:
                # Открываем новую сессию и начинаем транзакцию для изменения статуса на "в работе"
                session_work = Session()
                order_work = session_work.query(Order).get(order.id)
                order_work.status = 'в работе'
                try:
                    session_work.commit()
                except SQLAlchemyError as error:
                    session_work.rollback()
                    raise error
                finally:
                    session_work.close()

                time.sleep(10)  # Задержка для имитации обработки заказа

                # Открываем еще одну сессию и начинаем транзакцию для изменения статуса на "выполнен"
                session_complete = Session()
                order_complete = session_complete.query(Order).get(order.id)
                order_complete.status = 'выполнен'
                try:
                    session_complete.commit()
                except SQLAlchemyError as error:
                    print("НАЕБНУЛОСЬ")
                    session_complete.rollback()
                    raise error
                finally:
                    session_complete.close()

    except SQLAlchemyError as error:
        print("Ошибка при работе с базой данных:", error)

        if session:
            session.rollback()

    finally:
        if session:
            session.close()


start_order_processing()
