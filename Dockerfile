FROM python:3.11

#RUN apt update && apt upgrade -y
#RUN apt install -y poppler-utils

COPY src /app/src
COPY run_app.py /app/run_app.py
COPY pyproject.toml /app/pyproject.toml
COPY uv.lock /app/uv.lock
COPY .env /app/.env
COPY .config /app/.config
WORKDIR /app
RUN mkdir -p /app/temp/pdf && mkdir -p /app/temp/image

RUN pip install uv
RUN uv sync --frozen
ENTRYPOINT [ "uv", "run","run_app.py" ]


