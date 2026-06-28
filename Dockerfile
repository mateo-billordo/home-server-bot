FROM docker:cli AS docker-cli

FROM python:3.11-slim

COPY --from=docker-cli /usr/local/bin/docker /usr/local/bin/docker

RUN apt-get update && apt-get install -y --no-install-recommends \
    etherwake \
    iputils-ping \
    iproute2 \
    wireguard-tools \
    procps \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir pyTelegramBotAPI python-dotenv psutil

COPY bot/ bot/
COPY messages.json ./

CMD ["python", "-m", "bot.main"]
