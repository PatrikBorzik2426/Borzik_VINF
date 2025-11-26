FROM python:3.11-alpine

WORKDIR /app

RUN apk add --no-cache --virtual .build-deps gcc musl-dev && \
    pip install --no-cache-dir nltk pandas && \
    python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')" && \
    apk del .build-deps

COPY . .

CMD ["tail", "-f", "/dev/null"]