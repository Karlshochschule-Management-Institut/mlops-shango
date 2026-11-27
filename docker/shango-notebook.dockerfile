FROM python:3.14-slim

WORKDIR /work

COPY ./src/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN useradd --create-home kurs

USER kurs

EXPOSE 8888

CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser"]
