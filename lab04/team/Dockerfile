# Team-Image für pipeline.py (Strombedarfsanalyse)
# KI-Kennzeichnung (0RWX, https://0rwx.com/): WRITE (AI COLLABORATION), Claude Opus 5.5.
# Prompts: "get a dockerfile to run it", requirements.txt von Tag 4 eingefügt
#
# Bauen:    docker build -t team-dev:0.1 .
# Starten:  docker run --rm --mount "type=bind,src=.,target=/work" team-dev:0.1
# Jupyter:  docker run --rm -p 8888:8888 --mount "type=bind,src=.,target=/work" team-dev:0.1 \
#             jupyter lab --ip=0.0.0.0 --allow-root --no-browser
FROM python:3.12.8-slim

WORKDIR /work
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Bei Bind-Mount überdeckt; ohne Mount läuft die eingebaute Kopie
COPY pipeline.py .
CMD ["python", "pipeline.py"]
