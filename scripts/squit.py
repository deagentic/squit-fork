#!/usr/bin/env python3
"""
SQUIT CLI - Democratizando código SQL legacy con IA.

Uso:
    python3 scripts/squit.py
"""

import os
import sys
import time
from pathlib import Path

# Cargar .env
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                value = value.strip('"').strip("'")
                if key == 'GOOGLE_APPLICATION_CREDENTIALS' and not value.startswith('/'):
                    value = str((Path(__file__).parent.parent / value).absolute())
                os.environ[key] = value

sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

import warnings
warnings.filterwarnings('ignore')
import logging
logging.basicConfig(level=logging.ERROR, format='')

from agentic_adk import MasterAgent


def print_banner():
    """Banner ASCII art de SQUIT."""
    banner = """
    ███████╗ ██████╗ ██╗   ██╗██╗████████╗
    ██╔════╝██╔═══██╗██║   ██║██║╚══██╔══╝
    ███████╗██║   ██║██║   ██║██║   ██║   
    ╚════██║██║▄▄ ██║██║   ██║██║   ██║   
    ███████║╚██████╔╝╚██████╔╝██║   ██║   
    ╚══════╝ ╚══▀▀═╝  ╚═════╝ ╚═╝   ╚═╝   
    
          "SQL Quit" - Democratizando Código Legacy
          Búsqueda Inteligente | 2.9M Objetos SQL
          Powered by Gemini 2.5 Flash + Google ADK
          
                    Created by Karim Touma
    """
    print(banner)


class ProgressSpinner:
    """Spinner de progreso en la misma línea estilo CLI moderno."""
    
    def __init__(self):
        self.frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.current = 0
        self.last_length = 0
    
    def update(self, message: str):
        """Actualiza mensaje en la misma línea."""
        frame = self.frames[self.current % len(self.frames)]
        self.current += 1
        
        # Calcular espacios necesarios para limpiar mensaje anterior
        current_length = len(message) + 4  # 4 = "  " + frame + " "
        padding = max(0, self.last_length - current_length)
        
        # \r regresa al inicio, \033[K limpia hasta el final
        print(f'\r  {frame} {message}{" " * padding}\033[K', end='', flush=True)
        
        self.last_length = current_length
    
    def done(self, message: str):
        """Mensaje final."""
        padding = max(0, self.last_length - len(message) - 4)
        print(f'\r  ✓ {message}{" " * padding}\033[K', flush=True)
        self.last_length = 0
    
    def error(self, message: str):
        """Mensaje de error."""
        padding = max(0, self.last_length - len(message) - 4)
        print(f'\r  ✗ {message}{" " * padding}\033[K', flush=True)
        self.last_length = 0


def process_with_progress(agent: MasterAgent, query: str) -> str:
    """Procesa query con indicadores de progreso contextuales."""
    spinner = ProgressSpinner()
    
    import threading
    import queue
    
    result_queue = queue.Queue()
    stop_spinner = threading.Event()
    
    def spin():
        """Thread del spinner con mensajes contextuales."""
        # Mensajes más específicos y contextuales
        stages = [
            f"Enriqueciendo '{query[:30]}' con catálogo de apps...",
            f"Buscando en 2.9M objetos SQL...",
            f"Analizando {query[:20]}... en código...",
            "Sintetizando respuesta con Gemini 2.5..."
        ]
        stage_idx = 0
        iterations = 0
        
        while not stop_spinner.is_set():
            spinner.update(stages[stage_idx])
            time.sleep(0.15)
            iterations += 1
            
            # Cambiar de etapa cada 1.5 segundos (10 iteraciones * 0.15s)
            if iterations % 10 == 0:
                stage_idx = min(stage_idx + 1, len(stages) - 1)
    
    def execute():
        """Thread de ejecución."""
        try:
            response = agent.process(query, show_progress=False)
            result_queue.put(('success', response))
        except Exception as e:
            result_queue.put(('error', str(e)))
    
    # Iniciar threads
    spinner_thread = threading.Thread(target=spin, daemon=True)
    exec_thread = threading.Thread(target=execute, daemon=True)
    
    spinner_thread.start()
    exec_thread.start()
    
    # Esperar resultado (con timeout de 60 segundos)
    exec_thread.join(timeout=60)
    stop_spinner.set()
    spinner_thread.join(timeout=0.5)
    
    # Verificar si terminó
    if not exec_thread.is_alive():
        # Obtener resultado
        try:
            status, result = result_queue.get_nowait()
            
            if status == 'success':
                spinner.done("Respuesta lista                              ")
                return result
            else:
                spinner.error(f"Error: {result[:50]}...")
                return f"❌ Error: {result}"
        except queue.Empty:
            spinner.error("Sin respuesta")
            return "❌ No se obtuvo respuesta del agente"
    else:
        spinner.error("Timeout (60s)")
        return "❌ Timeout: El agente tardó demasiado. Intenta una query más simple."


def main():
    """CLI principal."""
    # Banner
    print_banner()
    
    # Validar configuración
    required_vars = ['GEMINI_API_KEY', 'GOOGLE_CLOUD_PROJECT']
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        print(f"❌ Faltan variables: {', '.join(missing)}")
        print("\n💡 Configura en .env")
        return 1
    
    # Inicializar agente
    print("\n  Inicializando agente con Google ADK + Gemini 2.5...", end='', flush=True)
    try:
        agent = MasterAgent()
        print("\r  ✓ Agente listo                                          ")
    except Exception as e:
        print(f"\r  ✗ Error: {e}")
        return 1
    
    # REPL con memoria
    print("\n  💬 Conversación con memoria multi-turn activada")
    print("  Escribe tu pregunta sobre código SQL (o 'exit' para salir)")
    print("  Comandos: 'reset' para limpiar memoria, 'exit' para salir")
    print("  Ejemplos: kayak, inventario, fechas, CVtaVentasSel")
    print()
    
    turn_count = 0
    
    while True:
        try:
            # Prompt minimalista con contador de turno
            turn_count += 1
            query = input(f"\n\033[1;36msquit[{turn_count}]>\033[0m ").strip()
            
            if not query:
                turn_count -= 1
                continue
            
            if query.lower() in ['exit', 'quit', 'salir', 'q']:
                print("\n  👋 ¡Hasta luego!")
                break
            
            # Comando para reiniciar conversación
            if query.lower() in ['reset', 'clear', 'reiniciar']:
                agent.reset_conversation()
                turn_count = 0
                print("\n  🔄 Memoria limpiada. Nueva conversación iniciada.")
                continue
            
            # Procesar con progreso
            print()
            response = process_with_progress(agent, query)
            
            # Mostrar respuesta
            print()
            print(response)
            
        except KeyboardInterrupt:
            print("\n\n  👋 ¡Hasta luego!")
            break
        except Exception as e:
            print(f"\n  ❌ Error: {e}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())