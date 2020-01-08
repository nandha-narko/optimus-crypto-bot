FROM python:3.8

RUN mkdir -p /var/optimus-crypto-bot

WORKDIR /var/optimus-crypto-bot

COPY ./ /var/optimus-crypto-bot

RUN pip install -r requirements.txt

ENTRYPOINT python /var/optimus-crypto-bot/app.py