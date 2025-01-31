# ./api/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from kafka import KafkaProducer
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

producer = KafkaProducer(
    bootstrap_servers=['kafka:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    api_version=(0, 10, 1)
)

@app.route('/pedidos', methods=['POST'])
def crear_pedido():
    try:
        pedido = request.json
        
        # Validar que todos los campos requeridos estén presentes
        required_fields = ['sucursal', 'producto', 'cantidad', 'total', 'fecha']
        for field in required_fields:
            if field not in pedido:
                return jsonify({"error": f"Falta el campo {field}"}), 400

        # Validar el formato de la fecha
        try:
            fecha = datetime.strptime(pedido['fecha'], '%Y-%m-%d %H:%M:%S')
            pedido['fecha'] = fecha.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            return jsonify({
                "error": "Formato de fecha inválido. Use YYYY-MM-DD HH:MM:SS"
            }), 400

        producer.send('pedidos', pedido)
        producer.flush()
        return jsonify({"message": "Pedido recibido"}), 201
        
    except Exception as e:
        print(f"Error en crear_pedido: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)