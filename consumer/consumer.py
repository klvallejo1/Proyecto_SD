# ./consumer/consumer.py
from kafka import KafkaConsumer
import json
import mysql.connector
from datetime import datetime
import time

def connect_db():
    print("\n=== Intentando conectar a la base de datos ===")
    try:
        conn = mysql.connector.connect(
            host="mysql",
            user="root",
            password="root",
            database="pedidos_db"
        )
        print("✅ Conexión exitosa a la base de datos")
        return conn
    except Exception as e:
        print(f"❌ Error al conectar a la base de datos: {e}")
        raise

def init_db():
    print("\n=== Inicializando la base de datos ===")
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pedidos (
                id INT AUTO_INCREMENT PRIMARY KEY,
                sucursal VARCHAR(255) NOT NULL,
                producto VARCHAR(255) NOT NULL,
                cantidad INT NOT NULL,
                total DECIMAL(10,2) NOT NULL,
                fecha DATETIME NOT NULL
            )
        ''')
        
        conn.commit()
        print("✅ Tabla pedidos creada o verificada exitosamente")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"❌ Error al inicializar la base de datos: {e}")
        raise

def store_pedido(pedido):
    print(f"\n=== Intentando almacenar pedido: {pedido} ===")
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        query = '''
            INSERT INTO pedidos (sucursal, producto, cantidad, total, fecha)
            VALUES (%s, %s, %s, %s, %s)
        '''
        values = (
            pedido['sucursal'],
            pedido['producto'],
            pedido['cantidad'],
            pedido['total'],
            pedido['fecha']
        )
        
        print(f"Query a ejecutar: {query}")
        print(f"Valores: {values}")
        
        cursor.execute(query, values)
        conn.commit()
        
        inserted_id = cursor.lastrowid
        print(f"✅ Pedido insertado con ID: {inserted_id}")
        
        # Verificar la inserción
        cursor.execute("SELECT * FROM pedidos WHERE id = %s", (inserted_id,))
        result = cursor.fetchone()
        print(f"✅ Verificación de inserción: {result}")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error al almacenar pedido: {e}")
        print(f"Tipo de error: {type(e)}")
        return False

def main():
    print("\n=== Iniciando consumidor de Kafka ===")
    time.sleep(10)  # Esperar a que Kafka esté listo
    
    try:
        consumer = KafkaConsumer(
            'pedidos',
            bootstrap_servers=['kafka:9092'],
            group_id='pedidos_group',
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            api_version=(0, 10, 1)
        )
        
        init_db()
        print("✅ Consumidor iniciado correctamente")
        print("=== Comenzando a consumir mensajes ===")
        
        for message in consumer:
            print(f"\n📨 Mensaje recibido de Kafka:")
            print(f"Topic: {message.topic}")
            print(f"Partición: {message.partition}")
            print(f"Offset: {message.offset}")
            print(f"Valor: {message.value}")
            
            if store_pedido(message.value):
                print("✅ Mensaje procesado y guardado exitosamente")
            else:
                print("❌ Error al procesar el mensaje")
                
    except Exception as e:
        print(f"❌ Error al consumir mensajes: {e}")
        raise

if __name__ == "__main__":
    print("\n=== Iniciando programa principal del consumer ===")
    while True:
        try:
            main()
        except Exception as e:
            print(f"\n❌ Error en el programa principal: {e}")
            print("⏲️ Reintentando en 5 segundos...")
            time.sleep(5)