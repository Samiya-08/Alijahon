FROM python:3.12-alpine

WORKDIR app/

COPY . .
RUN pip install -r req.txt