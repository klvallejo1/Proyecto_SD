from flask import Flask, render_template, jsonify
from flask_cors import CORS
import mysql.connector
from datetime import datetime
import logging

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.DEBUG)

def get_db_connection():
    return mysql.connector.connect(
        host="mysql",
        user="root",
        password="root",
        database="pedidos_db"
    )

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/pedidos')
def get_pedidos():
    try:
        app.logger.info("Obteniendo todos los pedidos")
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute('''
            SELECT 
                id,
                sucursal,
                producto,
                cantidad,
                total,
                fecha
            FROM pedidos 
            ORDER BY fecha DESC
        ''')
        
        pedidos = cursor.fetchall()
        app.logger.info(f"Encontrados {len(pedidos)} pedidos")
        
        for pedido in pedidos:
            if isinstance(pedido['fecha'], datetime):
                pedido['fecha'] = pedido['fecha'].strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.close()
        conn.close()
        
        return jsonify(pedidos)
    except Exception as e:
        app.logger.error(f"Error al obtener pedidos: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/pedidos/sucursal/<sucursal>')
def get_pedidos_por_sucursal(sucursal):
    try:
        app.logger.info(f"Obteniendo pedidos para sucursal: {sucursal}")
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute('''
            SELECT 
                id,
                sucursal,
                producto,
                cantidad,
                total,
                fecha
            FROM pedidos 
            WHERE sucursal = %s
            ORDER BY fecha DESC
        ''', (sucursal,))
        
        pedidos = cursor.fetchall()
        app.logger.info(f"Encontrados {len(pedidos)} pedidos para sucursal {sucursal}")
        
        for pedido in pedidos:
            if isinstance(pedido['fecha'], datetime):
                pedido['fecha'] = pedido['fecha'].strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.close()
        conn.close()
        
        return jsonify(pedidos)
    except Exception as e:
        app.logger.error(f"Error al obtener pedidos por sucursal: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)