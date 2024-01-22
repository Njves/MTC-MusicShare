FROM python:3.10-alpine

RUN adduser -D chat

WORKDIR /home/chat

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt && pip install gunicorn
RUN mkdir -p /app/content
COPY app app
COPY main.py config.py boot.sh ./
RUN chmod +x boot.sh

ENV FLASK_APP main.py

RUN chown -R chat:chat ./
USER chat

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]