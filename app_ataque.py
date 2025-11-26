"""
Interfaz Web para FSM Naval Battle - Cliente de Ataque
Integra la lógica FSM existente con una interfaz web usando Flask
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import socket

app = Flask(__name__)
CORS(app)

class NavalClientFSM:
    """
    Implementación de la Máquina de Estados Finitos para el cliente de ataque naval.
    """
    INICIO = 'q0'
    ATACANDO = 'q1'
    VICTORIA = 'q2'
    DERROTA = 'q3'
    
    def __init__(self):
        self.estado_actual = self.INICIO
        self.tablero_ataques = {
            'A1': '~', 'A2': '~', 'A3': '~', 'A4': '~', 'A5': '~',
            'B1': '~', 'B2': '~', 'B3': '~', 'B4': '~', 'B5': '~',
            'C1': '~', 'C2': '~', 'C3': '~', 'C4': '~', 'C5': '~',
            'D1': '~', 'D2': '~', 'D3': '~', 'D4': '~', 'D5': '~',
            'E1': '~', 'E2': '~', 'E3': '~', 'E4': '~', 'E5': '~'
        }
        self.server_host = 'localhost'
        self.server_port = 5001
        self.ataques_realizados = 0
        self.barcos_hundidos = 0
        
    def enviar_ataque(self, coordenada):
        try:
            if coordenada not in self.tablero_ataques:
                return None
                
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(5)
            client_socket.connect((self.server_host, self.server_port))
            
            client_socket.send(coordenada.encode())
            response = client_socket.recv(1024).decode()
            client_socket.close()
            
            self.ataques_realizados += 1
            self._procesar_respuesta(coordenada, response)
            
            return response
            
        except ConnectionRefusedError:
            return "ERROR:No se pudo conectar al servidor"
        except Exception as e:
            return f"ERROR:{str(e)}"
    
    def _procesar_respuesta(self, coordenada, respuesta):
        codigo, mensaje = respuesta.split(':', 1)
        
        if self.estado_actual == self.INICIO:
            self.estado_actual = self.ATACANDO
        
        if self.estado_actual == self.ATACANDO:
            if codigo == "200" and "Hundido" in mensaje:
                self.tablero_ataques[coordenada] = 'X'
                self.barcos_hundidos += 1
                self.estado_actual = self.VICTORIA
                
            elif codigo == "202" and "Impactado" in mensaje:
                self.tablero_ataques[coordenada] = 'X'
                
            elif codigo == "404" and "Fallido" in mensaje:
                self.tablero_ataques[coordenada] = 'O'
                
            elif "404" in codigo and coordenada not in self.tablero_ataques:
                self.ataques_realizados -= 1

# Instancia global del cliente FSM
cliente = NavalClientFSM()

@app.route('/')
def index():
    return render_template('ataque.html')

@app.route('/configurar', methods=['POST'])
def configurar():
    data = request.json
    cliente.server_host = data.get('host', 'localhost')
    cliente.server_port = int(data.get('port', 5001))
    return jsonify({'success': True, 'host': cliente.server_host, 'port': cliente.server_port})

@app.route('/atacar', methods=['POST'])
def atacar():
    data = request.json
    coordenada = data.get('coordenada')
    
    respuesta = cliente.enviar_ataque(coordenada)
    
    return jsonify({
        'respuesta': respuesta,
        'tablero': cliente.tablero_ataques,
        'estado': cliente.estado_actual,
        'ataques': cliente.ataques_realizados,
        'hundidos': cliente.barcos_hundidos
    })

@app.route('/estado', methods=['GET'])
def obtener_estado():
    return jsonify({
        'tablero': cliente.tablero_ataques,
        'estado': cliente.estado_actual,
        'ataques': cliente.ataques_realizados,
        'hundidos': cliente.barcos_hundidos
    })

@app.route('/reiniciar', methods=['POST'])
def reiniciar():
    global cliente
    cliente = NavalClientFSM()
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)