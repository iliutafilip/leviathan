FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 2222

CMD ["python", "leviathan.py", "-a", "0.0.0.0", "-p", "2222", "-s"]

RUN python -m unittest discover tests

RUN mkdir -p /app/configs \
 && test -f /app/configs/server.key || ssh-keygen -t rsa -b 2048 -f /app/configs/server.key -N ""

