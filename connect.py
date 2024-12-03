from OP1 import Client

# Укажите адрес вашего OPC UA сервера
url = "opc.tcp://localhost:53530/OPCUA/SimulationServer"

# Создайте клиента
client = Client(url)

try:
    # Подключитесь к серверу
    client.connect()
    print("Успешное подключение к OPC UA серверу!")

    # Получите корневой узел
    root = client.get_root_node()
    print("Корневой узел:", root)

    # Укажите путь к узлу, который хотите считать
    # Например, замените на ваш путь
    node_id = "ns=3;i=1008"  # Измените на ID вашего узла
    node = client.get_node(node_id)

    # Чтение значения узла
    value = node.get_value()
    print(f"Значение узла {node_id}: {value}")

except Exception as e:
    print(f"Ошибка: {e}")
finally:
    # Закройте соединение
    client.disconnect()
