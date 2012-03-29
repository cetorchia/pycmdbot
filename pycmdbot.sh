#!/bin/sh
cd ~/pycmdbot

# Check if they are already running
IS_CTORCHIA87="$(ps -e e | grep -P '\d python pycmdbot.py -um -c conf/ctorchia87.cfg' | wc -l)"
IS_PYCMDBOT="$(ps -e e | grep -P '\d python pycmdbot.py -a -c conf/pycmdbot.cfg' | wc -l)"

# Run the command bots

DATE="$(date +%Y%m%d%H%M%S)"

if [ $IS_CTORCHIA87 -eq 0 ]; then
  python pycmdbot.py -um -c conf/ctorchia87.cfg -l log/ctorchia87.log$DATE 1> /dev/null 2> /dev/null &
fi

if [ $IS_PYCMDBOT -eq 0 ]; then
  python pycmdbot.py -a -c conf/pycmdbot.cfg -l log/pycmdbot.log$DATE 1> /dev/null 2> /dev/null &
fi
