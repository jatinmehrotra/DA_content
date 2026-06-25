FROM public.ecr.aws/lambda/microvms:al2023-minimal

# System dependencies (curl-minimal is already in the base image)
RUN microdnf install -y python3 python3-pip git && microdnf clean all

# Python packages available to AI-generated code
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code executor
WORKDIR /sandbox
COPY executor.py .

EXPOSE 8080

CMD ["python3", "executor.py"]
