#  FSM Naval Battle - Batalla Naval con Máquinas de Estados Finitos

Un juego interactivo de batalla naval implementado con **Máquinas de Estados Finitos (FSM)** que demuestra conceptos de teoría de autómatas, comunicación cliente-servidor TCP/IP y programación web en tiempo real.

##  Descripción del Proyecto

**FSM Naval Battle** es una aplicación educativa que simula un sistema de defensa naval donde:
- Un **servidor (flota)** maneja 3 embarcaciones y responde a ataques usando una máquina de estados finitos
- Un **cliente (ataque)** realiza ataques coordinados a través de sockets TCP
- Una **interfaz web** en tiempo real muestra el estado del juego con SSE (Server-Sent Events)

### Máquinas de Estados Finitos Implementadas

#### **Servidor (Defensa Naval)**
```
Estados: q0 (Inicio) → q1 (Flota Intacta) → q2 (Hundido - Final)
Transiciones:
- Ataque al agua (404): q1 → q1
- Impacto en barco (202): q1 → q1
- Barco hundido (200): q1 → q1
- Toda la flota destruida (500): q1 → q2 ✓
```

#### **Cliente (Ataque)**
```
Estados: q0 (Inicio) → q1 (Atacando) → q2 (Victoria - Final)
Transiciones:
- Configurar conexión: q0 → q1
- Ataque rechazado: q1 → q1
- Ataque aceptado: q1 → q1
- Flota enemiga hundida: q1 → q2 ✓
```

##  Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                     ARQUITECTURA FSM NAVAL BATTLE           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐        ┌──────────────────────────┐  │
│  │   CLIENTE HTTP  │        │  SERVIDOR FLASK (5003)  │  │
│  │  (Puerto 5000)  │◄──────►│   + Web Interface SSE   │  │
│  └─────────────────┘        └──────────────────────────┘  │
│         ▲                            ▲                      │
│         │                            │                      │
│    Browser/UI                  Evento de Ataque            │
│         │                            │                      │
│         │                    ┌───────▼──────────┐           │
│         │                    │  FSM Naval Server│           │
│         │                    │  (Flota + FSM)   │           │
│         │                    └───────┬──────────┘           │
│         │                            │                      │
│  ┌──────▼─────────────────────────────────────┐            │
│  │   CLIENTE ATAQUE (Python)                  │            │
│  │   - Socket TCP port 5001                   │            │
│  │   - Envía coordenadas (A1, B3, etc.)       │            │
│  └──────────────────────────────────────────┘            │
│         ▲                                                   │
│         │                                                   │
│    Socket TCP                                              │
│    (puerto 5001)                                            │
└─────────────────────────────────────────────────────────────┘
```

##  Características Principales

-  **Máquinas de Estados Finitos** con transiciones definidas formalmente
-  **Comunicación TCP/IP** entre cliente y servidor
-  **Interfaz Web Responsiva** con diseño adaptativo (mobile, tablet, desktop)
-  **Tiempo Real** con SSE (Server-Sent Events)
-  **3 Embarcaciones**: Destroyer (1 celda), Submarine (2 celdas), Battleship (3 celdas)
-  **Tablero 5×5** de defensa y ataque
-  **Colocación Automática** de flota al iniciar
-  **Respuestas con Códigos HTTP**: 200 (hundido), 202 (impacto), 404 (agua), 500 (fin del juego)
-  **Estadísticas en Vivo**: ataques recibidos, último ataque, estado de barcos

##  Instalación

### Requisitos
- **Python 3.7+**
- **pip** (gestor de paquetes)

### Pasos

1. **Clonar o descargar el repositorio**
   ```bash
   git clone https://github.com/tu-usuario/fsm-naval-battle.git
   cd fsm-naval-battle
   ```

2. **Crear entorno virtual** (recomendado)
   ```bash
   python -m venv .venv
   ```

3. **Activar entorno virtual**
   - En Windows (PowerShell):
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```
   - En macOS/Linux:
     ```bash
     source .venv/bin/activate
     ```

4. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

##  Uso

### Opción 1: Ejecutar Servidor Web (Modo Interfaz Gráfica)

```bash
python app_flota.py
```
Luego abre en tu navegador: **http://localhost:5003**

### Opción 2: Ejecutar Cliente de Ataque (Modo Interfaz Gráfica)

En otra terminal:
```bash
python app_ataque.py
```
Luego abre en tu navegador: **http://localhost:5002**

El ataque se hace por defecto a **localhost:5001**

Así que configura la IP y puerto del servidor, luego selecciona coordenadas para atacar.


##  Estructura del Proyecto

```
ProyectoBatallaNaval/
├── README.md                          # Este archivo
├── requirements.txt                   # Dependencias Python
├── app_flota.py                       # Servidor Flask (web + FSM)
├── app_ataque.py                      # Cliente de ataque (terminal)
└── templates/
    ├── flota.html                     # Interfaz web del servidor
    └── ataque.html                    # Interfaz web del cliente
```
##  Códigos de Respuesta del Servidor

| Código | Significado | Transición |
|--------|-------------|-----------|
| **200** | Barco hundido | q1 → q1 (Aceptado) |
| **202** | Impacto en barco | q1 → q1 (Aceptado) |
| **404** | Ataque fallido (agua) | q1 → q1 (Rechazado) |
| **500** | Flota completamente destruida | q1 → q2 (Fin) |

##  Conceptos Teóricos

### Máquina de Estados Finitos (FSM / DFA)
- **Q** (Estados): {q0, q1, q2}
- **Σ** (Alfabeto): {A1, A2, ..., E5} (coordenadas del tablero)
- **δ** (Función de transición): Depende del resultado del ataque
- **q₀** (Estado inicial): q0
- **F** (Estados de aceptación): {q2}

### Comunicación TCP/IP
- **Socket Server**: Escucha en puerto 5001
- **Protocolo**: TCP con formato `coordenada` → `código:mensaje`
- **Manejo de conexiones**: Múltiples ataques simultáneos con threading

### Tiempo Real Web
- **SSE (Server-Sent Events)**: Conexión unidireccional servidor → cliente
- **Actualización automática**: Sin necesidad de polling manual

##  Dependencias

```
flask==2.3.3
flask-cors==4.0.0
requests==2.31.0
```

Ver `requirements.txt` para detalles completos.

##  Diseño Responsivo

- **Mobile** (≤700px): Layout apilado, celdas compactas
- **Tablet** (700px - 1200px): Layout dos columnas (texto/matriz), celdas medianas
- **Desktop** (≥1200px): Layout optimizado, celdas grandes (96px)

Variables CSS para ajustar:
```css
:root {
    --cell-size: 96px;      /* Tamaño de cada celda */
    --tab-gap: 14px;        /* Espaciado entre celdas */
}
```

##  Cómo Jugar

1. **Abre el servidor**: `python app_flota.py`
2. **Accede a la web**: http://localhost:5003
3. **Observa la flota**: Destroyer (D), Submarine (S), Battleship (B) colocados aleatoriamente
4. **Inicia un ataque, ejecuta**: `python app_ataque.py` 
5. **Accede a la web**: http://localhost:5003, por defecto ataca a la flota en localhost:5001
5. **Repite** hasta hundir toda la flota
6. **¡Victoria!** Cuando recibas el código 500


##  Referencias y Recursos

- [Teoría de Autómatas y Lenguajes Formales](https://en.wikipedia.org/wiki/Deterministic_finite_automaton)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Python Socket Programming](https://docs.python.org/3/library/socket.html)
- [Server-Sent Events (SSE)](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)

##  Contribuciones

Las contribuciones son bienvenidas. Por favor:
1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

##  Autor

Desarrollado como proyecto educativo para **Matemáticas para la Informática** en ITM.

##  Ideas Futuras

- [ ] Modo multijugador real (dos jugadores compitiendo)
- [ ] Base de datos para registrar resultados
- [ ] Modo IA para jugar contra la computadora
- [ ] Animaciones mejoradas de explosiones
- [ ] Sistema de chat en tiempo real
- [ ] Replay de partidas guardadas
- [ ] Soporte para diferentes tamaños de tablero

##  Reporte de Bugs

Si encuentras algún bug, por favor abre un issue en GitHub describiendo:
- El problema
- Pasos para reproducirlo
- Comportamiento esperado vs. observado
- Tu sistema operativo y versión de Python

---

**Última actualización**: Noviembre 2025

