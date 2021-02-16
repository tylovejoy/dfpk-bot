FROM python:3.9

WORKDIR /usr/src/app

# For safety reason, create an user with lower privileges than root and run from there
RUN useradd -m -d /home/dfpk-bot -s /bin/bash dfpk-bot

RUN mkdir /usr/src/dfpk-bot

RUN chown -R discordbot /usr/src/dfpk-bot
USER dfpk-bot

COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python3", "main.py" ]
