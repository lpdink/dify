docker pull registry.cn-hangzhou.aliyuncs.com/8bitpd/dify-api:0.6.15
docker tag registry.cn-hangzhou.aliyuncs.com/8bitpd/dify-api:0.6.15 langgenius/dify-api:0.6.15

docker pull registry.cn-hangzhou.aliyuncs.com/8bitpd/dify-web:0.6.15
docker tag registry.cn-hangzhou.aliyuncs.com/8bitpd/dify-web:0.6.15 langgenius/dify-web:0.6.15

docker pull registry.cn-hangzhou.aliyuncs.com/8bitpd/dify-sandbox:0.2.1
docker tag registry.cn-hangzhou.aliyuncs.com/8bitpd/dify-sandbox:0.2.1 langgenius/dify-sandbox:0.2.1

docker pull registry.cn-hangzhou.aliyuncs.com/8bitpd/postgres:15-alpine
docker tag registry.cn-hangzhou.aliyuncs.com/8bitpd/postgres:15-alpine postgres:15-alpine

docker pull registry.cn-hangzhou.aliyuncs.com/8bitpd/weaviate:1.19.0
docker tag registry.cn-hangzhou.aliyuncs.com/8bitpd/weaviate:1.19.0 semitechnologies/weaviate:1.19.0
