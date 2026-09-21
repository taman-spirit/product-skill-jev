FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends grep curl \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -r botuser && useradd -r -g botuser botuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py agent.py ./

RUN mkdir -p /workspace && chown botuser:botuser /workspace

USER botuser

HEALTHCHECK --interval=60s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import anthropic; print('ok')" || exit 1

CMD ["python", "-u", "bot.py"]
