FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    icecast2 \
    ffmpeg \
    && pip install highrise-bot-sdk yt-dlp \
    && apt-get clean

COPY icecast.xml /etc/icecast2/icecast.xml
COPY bot.py .
COPY start.sh .
RUN chmod +x start.sh

CMD ["./start.sh"]