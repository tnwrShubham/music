#!/bin/bash
# Start Icecast
icecast2 -c /etc/icecast2/icecast.xml &
sleep 2
# Start bot
python bot.py