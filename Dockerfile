# ============================================================
# OrçaObra AI — Imagem de produção
# ============================================================
FROM python:3.12-slim

# Evita buffering de logs no container
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# OpenBLAS pode estourar memória em containers com pouca RAM
ENV OPENBLAS_NUM_THREADS=1
ENV MKL_NUM_THREADS=1
ENV OMP_NUM_THREADS=1

WORKDIR /app

# Instala dependências do sistema (OpenCV precisa de libgl)
RUN apt-get update && apt-get install -y --no-install-recommends     libgl1-mesa-glx     libglib2.0-0     libsm6     libxext6     libxrender-dev     && rm -rf /var/lib/apt/lists/*

# Copia e instala dependências Python primeiro (cache de layer)
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código
COPY . .

# Cria diretórios de dados persistentes
RUN mkdir -p /app/orcamentos_salvos /app/perfil_empresa /app/.cache_ia

# Porta padrão do Streamlit
EXPOSE 8501

# Healthcheck simples
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3     CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" || exit 1

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
