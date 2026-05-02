FROM apache/spark:3.5.3

USER root

# Spark image ships Python 3.8; install pip + the libs the UDF needs.
RUN apt-get update && apt-get install -y --no-install-recommends python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --no-cache-dir \
    pyarrow==15.0.2 \
    pandas==2.0.3 \
    numpy==1.24.4 \
    typing-extensions==4.8.0 \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    torch \
    transformers

ENV PYTHONPATH=/opt/app
ENV PYSPARK_PYTHON=python3
ENV PYSPARK_DRIVER_PYTHON=python3
