import subprocess
import sys
import os
import webbrowser
import time

# Caminho para o dashboard.py (assume que está na mesma pasta)
dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard.py")

# Iniciar o streamlit num subprocesso
process = subprocess.Popen(
    [sys.executable, "-m", "streamlit", "run", dashboard_path, "--server.port", "8501"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

# Aguardar alguns segundos para o servidor iniciar
time.sleep(3)

# Abrir o navegador
webbrowser.open("http://localhost:8501")

# Manter o processo ativo
process.wait()