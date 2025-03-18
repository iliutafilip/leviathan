FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 22

CMD exec python leviathan.py -a 0.0.0.0 -p 22 -s
