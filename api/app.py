# ./api/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from kafka import KafkaProducer
import json
import mysql.connector
from datetime import datetime
import time

app = Flask(__name__)
CORS(app)

def get_kafka_producer():
    retries = 0
    max_retries = 3
    while retries < max_retries:
        try:
            producer = KafkaProducer(
                bootstrap_servers=['kafka:9092'],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',
                retries=3,
                retry_backoff_ms=1000,
                request_timeout_ms=5000,
                max_block_ms=5000,
                api_version=(0, 10, 1)
            )
            return producer
        except Exception as e:
            print(f"Error al conectar con Kafka (intento {retries + 1}): {e}")
            retries += 1
            time.sleep(5)
    raise Exception("No se pudo conectar con Kafka después de múltiples intentos")

@app.route('/pedidos', methods=['POST'])
def crear_pedido():
    try:
        pedido = request.json
        print(f"Recibido pedido: {pedido}")
        
        producer = get_kafka_producer()
        future = producer.send('pedidos', pedido)
        
        try:
            record_metadata = future.get(timeout=5)
            print(f"Mensaje enviado - Tópico: {record_metadata.topic}, Partición: {record_metadata.partition}, Offset: {record_metadata.offset}")
            producer.flush(timeout=5)
            producer.close(timeout=5)
            return jsonify({"message": "Pedido recibido"}), 201
        except Exception as e:
            print(f"Error al enviar mensaje a Kafka: {e}")
            return jsonify({"error": str(e)}), 500
            
    except Exception as e:
        print(f"Error en crear_pedido: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/pedidos', methods=['GET'])
def obtener_pedidos():
    try:
        conn = mysql.connector.connect(
            host="mysql",
            user="root",
            password="root",
            database="pedidos_db"
        )
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute('SELECT * FROM pedidos ORDER BY fecha DESC')
        pedidos = cursor.fetchall()
        
        for pedido in pedidos:
            if isinstance(pedido['fecha'], datetime):
                pedido['fecha'] = pedido['fecha'].strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.close()
        conn.close()
        
        return jsonify(pedidos)
    except Exception as e:
        print(f"Error al obtener pedidos: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)