import sys
import os
from pathlib import Path

# Adicionar o diretório pai ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configurar variáveis de ambiente antes de importar
os.environ.setdefault('FLASK_ENV', 'production')

from app import app as application

# Variável para WSGI
app = application

