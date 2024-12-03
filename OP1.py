from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import pandas as pd
from opcua import Client
import logging
import time
from threading import Thread

app = Flask(__name__)
socketio = SocketIO(app)

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Функция для подключения и получения данных с Prosys OPC UA Simulation Server
def get_opc_data():
    url = "opc.tcp://localhost:53530/OPCUA/SimulationServer"
    client = Client(url)

    try:
        client.connect()
        logging.info("Успешное подключение к Prosys OPC UA Simulation Server.")

        # Подключаемся к двум узлам
        node1 = client.get_node("ns=3;i=1007")  # Первый узел
        node2 = client.get_node("ns=3;i=1001")  # Второй узел

        logging.info(f"Подключено к узлам: {node1}, {node2}")

        # Получаем значения с обоих узлов
        value1 = node1.get_value()
        value2 = node2.get_value()

        logging.info(f"Значение узла 1: {value1}, Значение узла 2: {value2}")

        timestamp = pd.Timestamp.now()  # Текущее время для метки времени
        return timestamp, value1, value2  # Возвращаем оба значения
    except Exception as e:
        logging.error(f"Ошибка при подключении к OPC UA серверу: {e}")
        return None, None, None
    finally:
        client.disconnect()

def background_task():
    data = {}  # Словарь для хранения данных
    while True:
        timestamp, value1, value2 = get_opc_data()
        if timestamp is not None and value1 is not None and value2 is not None:
            data['timestamp'] = str(timestamp)
            data['value1'] = value1
            data['value2'] = value2
            socketio.emit('update_data', data)  # Отправляем оба значения
        time.sleep(1)  # Обновлять данные каждые 1 секунды

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    logging.info("Клиент подключен")

# Запуск фонового потока для получения данных
thread = Thread(target=background_task)
thread.start()

if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
