"""
Interfaz Web para FSM Naval Battle - Servidor de Defensa
Sistema de 3 embarcaciones con FSM mejorada y actualización en tiempo real
"""

from flask import Flask, render_template, jsonify, Response
from flask_cors import CORS
import socket
import threading
import random
import time
import json
from queue import Queue

app = Flask(__name__)
CORS(app)

eventos_queue = Queue()

class NavalServerFSM:
    """
    Máquina de Estados Finitos para el servidor de defensa naval.
    Maneja 3 embarcaciones: Destructor (1), Submarino (2), Acorazado (3)
    """
    
    def __init__(self):
        self.filas = 5
        self.columnas = 5
        self.tablero = self._crear_tablero_vacio()
        self.impactos = self._crear_tablero_vacio()
        
        # Definición de barcos
        self.barcos = {
            'destroyer': {'nombre': 'Destroyer', 'tamaño': 1, 'casillas': [], 'impactos': set()},
            'submarine': {'nombre': 'Submarine', 'tamaño': 2, 'casillas': [], 'impactos': set()},
            'battleship': {'nombre': 'Battleship', 'tamaño': 3, 'casillas': [], 'impactos': set()}
        }
        
        self.ataques_recibidos = set()
        self.server_socket = None
        self.host = '0.0.0.0'
        self.port = 5001
        self.ultimo_ataque = None
        self.ultimo_resultado = None
        self.juego_terminado = False
        
    def _crear_tablero_vacio(self):
        """Crea un tablero vacío 5x5"""
        tablero = {}
        for fila in ['A', 'B', 'C', 'D', 'E']:
            for col in ['1', '2', '3', '4', '5']:
                tablero[fila + col] = '~'
        return tablero
    
    def _obtener_casillas_adyacentes(self, coord, direccion, tamaño):
        """Obtiene lista de casillas para colocar un barco"""
        fila = coord[0]
        col = int(coord[1])
        casillas = []
        
        if direccion == 'H':  # Horizontal
            for i in range(tamaño):
                if col + i > 5:
                    return None
                casillas.append(fila + str(col + i))
        else:  # Vertical
            filas = ['A', 'B', 'C', 'D', 'E']
            fila_idx = filas.index(fila)
            for i in range(tamaño):
                if fila_idx + i >= 5:
                    return None
                casillas.append(filas[fila_idx + i] + str(col))
        
        return casillas
    
    def _puede_colocar_barco(self, casillas):
        """Verifica si las casillas están libres"""
        if casillas is None:
            return False
        for casilla in casillas:
            if self.tablero[casilla] != '~':
                return False
        return True
    
    def colocar_flota_automatica(self):
        """Coloca los 3 barcos automáticamente en posiciones aleatorias"""
        orden = ['battleship', 'submarine', 'destroyer']
        
        for barco_id in orden:
            barco = self.barcos[barco_id]
            colocado = False
            intentos = 0
            max_intentos = 100
            
            while not colocado and intentos < max_intentos:
                fila = random.choice(['A', 'B', 'C', 'D', 'E'])
                col = random.randint(1, 5)
                coord_inicial = fila + str(col)
                direccion = random.choice(['H', 'V'])
                
                casillas = self._obtener_casillas_adyacentes(coord_inicial, direccion, barco['tamaño'])
                
                if self._puede_colocar_barco(casillas):
                    letra = barco_id[0].upper()
                    for casilla in casillas:
                        self.tablero[casilla] = letra
                    barco['casillas'] = casillas
                    colocado = True
                    print(f"{barco['nombre']} colocado en {casillas}")
                
                intentos += 1
            
            if not colocado:
                print(f"Error: No se pudo colocar {barco['nombre']}")
                return False
        
        return True
    
    def _verificar_flota_destruida(self):
        """Verifica si todos los barcos han sido hundidos"""
        for barco in self.barcos.values():
            if len(barco['impactos']) < barco['tamaño']:
                return False
        return True
    
    def procesar_ataque(self, coordenada):
        """Procesa un ataque y retorna el resultado según la FSM"""
        # Si el juego ya terminó, rechazar cualquier ataque
        if self.juego_terminado:
            return "500", "Juego terminado. Toda la flota ha sido destruida"
        
        if coordenada not in self.tablero:
            return "404", "fallido"
        
        # Verificar si ya fue atacada
        if coordenada in self.ataques_recibidos:
            return "404", "fallido"
        
        self.ataques_recibidos.add(coordenada)
        self.ultimo_ataque = coordenada
        
        # Verificar si impacta algún barco
        barco_impactado = None
        barco_nombre = None
        for barco_id, barco in self.barcos.items():
            if coordenada in barco['casillas']:
                barco_impactado = barco_id
                barco_nombre = barco['nombre']
                break
        
        # Agua - RECHAZADO
        if barco_impactado is None:
            self.impactos[coordenada] = 'O'
            resultado = "404", "fallido"
            self.ultimo_resultado = resultado
            self._notificar_evento('ataque', coordenada, resultado, None)
            return resultado
        
        # Impacto en barco
        barco = self.barcos[barco_impactado]
        barco['impactos'].add(coordenada)
        self.impactos[coordenada] = 'X'
        
        # Verificar si el barco está hundido
        if len(barco['impactos']) == barco['tamaño']:
            # Verificar si es el último barco (toda la flota destruida)
            if self._verificar_flota_destruida():
                self.juego_terminado = True
                resultado = "500", "Toda la flota ha sido destruida. Fin del juego"
            else:
                resultado = "200", f"hundido:{barco_nombre}"
        else:
            # ACEPTADO: IMPACTADO
            resultado = "202", f"impactado:{barco_nombre}"
        
        self.ultimo_resultado = resultado
        self._notificar_evento('ataque', coordenada, resultado, barco_nombre)
        return resultado
    
    def _notificar_evento(self, tipo, coordenada, resultado, barco_nombre):
        """Envía un evento a la cola para notificar a la interfaz web"""
        evento = {
            'tipo': tipo,
            'coordenada': coordenada,
            'resultado': resultado,
            'barco': barco_nombre,
            'estado_barcos': self.obtener_estado_barcos(),
            'tablero': dict(self.tablero),
            'impactos': dict(self.impactos),
            'ataques_totales': len(self.ataques_recibidos),
            'timestamp': time.time()
        }
        eventos_queue.put(evento)
    
    def obtener_estado_barcos(self):
        """Retorna el estado de cada barco"""
        estado = {}
        for barco_id, barco in self.barcos.items():
            total_impactos = len(barco['impactos'])
            estado[barco_id] = {
                'nombre': barco['nombre'],
                'tamaño': barco['tamaño'],
                'impactos': total_impactos,
                'hundido': total_impactos == barco['tamaño'],
                'casillas': barco['casillas']
            }
        return estado
    
    def iniciar_servidor_socket(self):
        """Inicia el servidor TCP para recibir ataques"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            print(f"Servidor socket escuchando en {self.host}:{self.port}")
            
            while True:
                client_socket, client_address = self.server_socket.accept()
                
                try:
                    data = client_socket.recv(1024).decode().strip()
                    print(f"Ataque recibido: {data}")
                    
                    codigo, respuesta = self.procesar_ataque(data)
                    client_socket.send(f"{codigo}:{respuesta}".encode())
                    print(f"Respuesta enviada: {codigo}:{respuesta}")
                    
                except Exception as e:
                    print(f"Error al procesar solicitud: {e}")
                finally:
                    client_socket.close()
        
        except Exception as e:
            print(f"Error en servidor socket: {e}")
        finally:
            if self.server_socket:
                self.server_socket.close()

# Instancia global del servidor FSM
servidor = NavalServerFSM()

@app.route('/')
def index():
    return render_template('flota.html')

@app.route('/info-servidor', methods=['GET'])
def obtener_info_servidor():
    """Retorna información del servidor TCP (IP y puerto)"""
    import socket
    try:
        # Obtener el nombre del host
        hostname = socket.gethostname()
        # Obtener la IP local
        ip_local = socket.gethostbyname(hostname)
    except:
        ip_local = "127.0.0.1"
        hostname = "localhost"
    
    return jsonify({
        'ip': ip_local,
        'puerto': servidor.port,
        'host': hostname
    })

@app.route('/estado', methods=['GET'])
def obtener_estado():
    return jsonify({
        'tablero': servidor.tablero,
        'impactos': servidor.impactos,
        'ultimo_ataque': servidor.ultimo_ataque,
        'ultimo_resultado': servidor.ultimo_resultado,
        'ataques_totales': len(servidor.ataques_recibidos),
        'barcos': servidor.obtener_estado_barcos()
    })

@app.route('/eventos')
def eventos_stream():
    """Server-Sent Events para actualización en tiempo real"""
    def generar_eventos():
        while True:
            if not eventos_queue.empty():
                evento = eventos_queue.get()
                yield f"data: {json.dumps(evento)}\n\n"
            time.sleep(0.05)
    
    return Response(generar_eventos(), mimetype='text/event-stream')

@app.route('/reiniciar', methods=['POST'])
def reiniciar():
    global servidor
    servidor = NavalServerFSM()
    
    # Limpiar la cola de eventos
    while not eventos_queue.empty():
        eventos_queue.get()
    
    # Colocar flota automáticamente
    exito = servidor.colocar_flota_automatica()
    
    if exito:
        print("Juego reiniciado - Flota colocada")
        for barco_id, barco in servidor.barcos.items():
            print(f"  {barco['nombre']}: {barco['casillas']}")
    
    evento_reinicio = {
        'tipo': 'reinicio',
        'coordenada': None,
        'resultado': ('REINICIO', 'Juego reiniciado'),
        'barco': None,
        'estado_barcos': servidor.obtener_estado_barcos(),
        'tablero': dict(servidor.tablero),
        'impactos': dict(servidor.impactos),
        'ataques_totales': 0,
        'timestamp': time.time()
    }
    eventos_queue.put(evento_reinicio)
    
    return jsonify({
        'success': exito,
        'barcos': servidor.obtener_estado_barcos()
    })

if __name__ == '__main__':
    # Colocar flota automáticamente al iniciar
    if servidor.colocar_flota_automatica():
        print("Flota inicial colocada:")
        for barco_id, barco in servidor.barcos.items():
            print(f"  {barco['nombre']}: {barco['casillas']}")
    
    # Iniciar servidor socket en un hilo separado
    socket_thread = threading.Thread(target=servidor.iniciar_servidor_socket, daemon=True)
    socket_thread.start()
    
    # Iniciar servidor Flask
    app.run(host='0.0.0.0', port=5003, debug=False, threaded=True)