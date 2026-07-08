# Imagem da aplicação STRIDE Threat Modeler.
# Base Python 3.12 (mesma versão usada localmente).
FROM python:3.12-slim

# Dependências de sistema:
# - libgl1 / libglib2.0-0: exigidas pelo opencv (dependência do ultralytics/YOLOv8)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instala o torch CPU-only ANTES do requirements. No PyPI, o torch padrão para
# Linux vem com CUDA (~2 GB); o índice /whl/cpu traz a build enxuta de CPU.
RUN pip install --no-cache-dir torch torchvision \
        --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código da aplicação (dados/pesos/relatórios entram via volumes no compose)
COPY . .

# Streamlit (8501) e API FastAPI (8000)
EXPOSE 8501 8000

# Comando padrão: interface Streamlit. A API é definida no docker-compose.
CMD ["streamlit", "run", "app/streamlit_app.py", \
     "--server.address=0.0.0.0", "--server.port=8501"]
