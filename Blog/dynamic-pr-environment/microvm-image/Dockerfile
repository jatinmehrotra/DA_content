FROM public.ecr.aws/lambda/microvms:al2023-minimal

# System deps
RUN microdnf install -y python3 python3-pip && microdnf clean all

# Python deps (pre-downloaded wheels — no PyPI download at build time)
COPY wheels/ /tmp/wheels/
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir --no-index --find-links=/tmp/wheels/ -r /tmp/requirements.txt \
    && rm -rf /tmp/wheels/ /tmp/requirements.txt

# App code
WORKDIR /app
COPY app.py .

EXPOSE 8080

CMD ["python3", "app.py"]
