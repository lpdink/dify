FROM langgenius/dify-api:0.6.11

RUN pip install alibabacloud_gpdb20160503 alibabacloud_tea_openapi

RUN pip install pydantic_settings novita-client

RUN rm -rf /app/api/migrations

COPY api /app/api

ENTRYPOINT ["/bin/bash"]