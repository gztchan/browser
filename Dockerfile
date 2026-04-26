FROM debian:bookworm-slim

# Essential packages
RUN apt-get update && apt-get install -y \
    debian-keyring \
    debian-archive-keyring \
    apt-transport-https \
    curl \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 libnspr4 libnss3 libatk-bridge2.0-0 libatk1.0-0 libatspi2.0-0 libcairo2 libcups2 libgbm1 libgtk-3-0 libpango-1.0-0 libvulkan1 libxcomposite1 libxkbcommon0 \
    xdg-utils \
    xvfb xauth x11vnc novnc websockify supervisor golang-go \
    --no-install-recommends && apt-get clean && rm -rf /var/lib/apt/lists/*

# Chrome
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt-get install -y ./google-chrome-stable_current_amd64.deb && \
    rm google-chrome-stable_current_amd64.deb

# uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    mv /root/.local/bin/uv /usr/local/bin/uv && \
    mv /root/.local/bin/uvx /usr/local/bin/uvx

WORKDIR /app

ENV NODE_ENV=production

COPY . .

RUN chmod +x /app/start.sh

RUN uv sync --no-cache

EXPOSE 8000 6080

CMD ["./start.sh"]