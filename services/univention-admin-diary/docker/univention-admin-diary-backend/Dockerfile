FROM alpine:edge

# need testing repo for py3-flask-sqlalchemy
RUN apk add --no-cache -X http://dl-cdn.alpinelinux.org/alpine/edge/testing/ \
    python3 \
    py3-psycopg2 \
    py3-mysqlclient \
    py3-flask \
    py3-flask-sqlalchemy \
    py3-gunicorn \
    py3-virtualenv

RUN virtualenv --system-site-packages /uadb/venv && /uadb/venv/bin/pip3 install flask-restplus Flask-HTTPAuth

WORKDIR /uadb

COPY *.py /uadb/

EXPOSE 8910

CMD ["/uadb/venv/bin/python", "/usr/bin/gunicorn", "-c", "gunicorn_config.py", "backend:app"]
