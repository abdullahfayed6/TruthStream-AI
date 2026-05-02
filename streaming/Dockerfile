FROM apache/spark:3.5.3

USER root

# Install pip + ML inference libraries
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

# Pre-download the Spark-Kafka connector into the local Ivy cache so that
# spark-submit --packages works without live Maven access at runtime.
RUN /opt/spark/bin/spark-submit \
    --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1 \
    --class org.apache.spark.examples.SparkPi \
    local:///opt/spark/examples/jars/spark-examples_2.12-3.5.3.jar 1 \
    > /dev/null 2>&1 || true

ENV PYTHONPATH=/opt/app
ENV PYSPARK_PYTHON=python3
ENV PYSPARK_DRIVER_PYTHON=python3
