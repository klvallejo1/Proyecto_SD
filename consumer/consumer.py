# ./consumer/consumer.py
from kafka import KafkaConsumer
import json
import mysql.connector
from datetime import datetime
import time
from mysql.connector import pooling

# Configuración del pool de conexiones
dbconfig = {
    "pool_name": "mypool",
    "pool_size": 5,
    "host": "mysql",
    "user": "root",
    "password": "root",
    "database": "pedidos_db"
}

try:
    connection_pool = mysql.connector.pooling.MySQLConnectionPool(**dbconfig)
except Exception as e:
    print(f"Error al crear el pool de conexiones: {e}")
    raise

def get_connection():
    return connection_pool.get_connection()

def init_db():
    print("Inicializando la base de datos...")
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pedidos (
                id INT AUTO_INCREMENT PRIMARY KEY,
                sucursal VARCHAR(255) NOT NULL,
                producto VARCHAR(255) NOT NULL,
                cantidad INT NOT NULL,
                total DECIMAL(10,2) NOT NULL,
                fecha DATETIME NOT NULL,
                INDEX idx_sucursal (sucursal),
                INDEX idx_fecha (fecha)
            )
        ''')
        
        conn.commit()
        cursor.close()
        conn.close()
        print("Base de datos inicializada correctamente")
    except Exception as e:
        print(f"Error al inicializar la base de datos: {e}")
        raise

def store_pedido(pedido):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        query = '''
            INSERT INTO pedidos (sucursal, producto, cantidad, total, fecha)
            VALUES (%s, %s, %s, %s, %s)
        '''
        
        values = (
            pedido['sucursal'],
            pedido['producto'],
            int(pedido['cantidad']),
            float(pedido['total']),
            datetime.now()
        )
        
        cursor.execute(query, values)
        conn.commit()
        
        inserted_id = cursor.lastrowid
        print(f"Pedido almacenado con ID: {inserted_id}")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error al almacenar pedido: {e}")
        return False

def main():
    print("Iniciando consumidor de Kafka...")
    
    consumer = KafkaConsumer(
        'pedidos',
        bootstrap_servers=['kafka:9092'],
        group_id='pedidos_group',
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        value_deserializer=lambda x: json.loads(x.decode('utf-8')),
        consumer_timeout_ms=1000,
        api_version=(0, 10, 1),
        fetch_max_wait_ms=500,  # Reducir el tiempo de espera para nuevos mensajes
        fetch_min_bytes=1,      # Procesar mensajes tan pronto como lleguen
    )
    
    init_db()
    print("Comenzando a consumir mensajes...")
    
    try:
        for message in consumer:
            print(f"Mensaje recibido: {message.value}")
            if store_pedido(message.value):
                consumer.commit()
                print("Mensaje procesado exitosamente")
    except Exception as e:
        print(f"Error al consumir mensajes: {e}")
        raise

if __name__ == "__main__":
    while True:
        try:
            main()
        except Exception as e:
            print(f"Error en el programa principal: {e}")
            time.sleep(5)