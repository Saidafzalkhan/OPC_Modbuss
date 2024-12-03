from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import pandas as pd
from opcua import Client
from pymodbus.client import ModbusTcpClient  # Для Modbus TCP
import logging
import time
from threading import Thread

app = Flask(__name__)
socketio = SocketIO(app)

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Конфигурация Modbus
MODBUS_HOST = "127.0.0.1"  # IP-адрес Modbus-сервера
MODBUS_PORT = 502          # Порт Modbus (по умолчанию 502)

# Функция для подключения и получения данных с Prosys OPC UA Simulation Server
def get_opc_data():
    url = "opc.tcp://localhost:53530/OPCUA/SimulationServer"
    client = Client(url)

    try:
        client.connect()
        logging.info("Успешное подключение к Prosys OPC UA Simulation Server.")

        # Подключаемся к двум узлам
        node1 = client.get_node("ns=3;i=1006")  # Первый узел
        node2 = client.get_node("ns=3;i=1008")  # Второй узел

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

# Функция для подключения и получения данных с Modbus
def get_modbus_data():
    client = ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT)
    try:
        if client.connect():
            logging.info("Успешное подключение к Modbus-серверу.")
            # Чтение данных из регистра Holding Register
            response = client.read_holding_registers(address=1, count=2)  # Адрес 1, читаем 2 регистра
            if not response.isError():
                value1, value2 = response.registers
                logging.info(f"Modbus данные: {value1}, {value2}")
                return value1, value2
            else:
                logging.error("Ошибка при чтении Modbus-регистров.")
                return None, None
        else:
            logging.error("Не удалось подключиться к Modbus-серверу.")
            return None, None
    except Exception as e:
        logging.error(f"Ошибка при работе с Modbus: {e}")
        return None, None
    finally:
        client.close()


def background_task():
    data = {}  # Словарь для хранения данных
    while True:
        # Получение данных с OPC
        timestamp, opc_value1, opc_value2 = get_opc_data()
        # Получение данных с Modbus
        modbus_value1, modbus_value2 = get_modbus_data()

        if timestamp is not None:
            data['timestamp'] = str(timestamp)
            if opc_value1 is not None and opc_value2 is not None:
                data['opc_value1'] = opc_value1
                data['opc_value2'] = opc_value2
            if modbus_value1 is not None and modbus_value2 is not None:
                data['modbus_value1'] = modbus_value1
                data['modbus_value2'] = modbus_value2
            socketio.emit('update_data', data)  # Отправляем данные
        time.sleep(3)  # Обновлять данные каждые 3 секунды

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
    logging.info("Запуск Flask-сервера...")
    try:
        socketio.run(app, host="0.0.0.0", port=5001, debug=True, allow_unsafe_werkzeug=True)
    except Exception as e:
        logging.error(f"Ошибка при запуске Flask: {e}")
