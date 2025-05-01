FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/configs

RUN useradd -m user
USER user

EXPOSE 2222

CMD ["python", "-u","leviathan.py", "-a", "0.0.0.0", "-p", "2222"]
