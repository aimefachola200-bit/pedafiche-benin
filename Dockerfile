FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PEDAFICHE_DB=/data/pedafiche.db PORT=8080
VOLUME /data
CMD ["sh", "-c", "waitress-serve --listen=0.0.0.0:$PORT --threads=8 wsgi:application"]
