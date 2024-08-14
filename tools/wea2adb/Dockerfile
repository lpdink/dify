# docker build . -t wea2adb:latest
FROM python:3.10.14-alpine

WORKDIR /migration

RUN pip install \
    weaviate-client==3.21.0 \
    psycopg2-binary==2.9.9 \
    pydantic==2.8.2 \
    alibabacloud_gpdb20160503==3.8.3 \
    alibabacloud_tea_openapi==0.3.10 \
    -i  https://pypi.tuna.tsinghua.edu.cn/simple

COPY *.py /migration/

ENTRYPOINT ["python", "main.py"]