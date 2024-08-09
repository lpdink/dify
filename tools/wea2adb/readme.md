# 从weaviate 迁移数据到adbpg

## 下载必要依赖

```sh
pip install weaviate-client==3.21.0 alibabacloud_gpdb20160503==3.8.3 alibabacloud_tea_openapi==0.3.10
```

## 拷贝数据，启动weaviate服务

拷贝您的weaviate向量数据到tools/wea2adb/weaviate，该向量数据位于dify/docker/volumes/weaviate

```
cp dify/docker/volumes/weaviate dify/tools/wea2adb/weaviate
```

启动weaviate服务，这会占用本地8080端口，且容器与宿主机共享网络环境，以便我们可以通过 http://127.0.0.1:8080 访问

```
cd dify/tools/wea2adb/
docker compose up
```

## 填写adbpg账户配置

打开./adbpg_env.sh，按照您的信息填写；

```sh
export ADBPG_ACCESS_KEY_ID=
export ADBPG_ACCESS_KEY_SECRET=
export ADBPG_REGION_ID=
export ADBPG_INSTANCE_ID=
export ADBPG_ACCOUNT=
export ADBPG_ACCOUNT_PASSWORD=
export ADBPG_NAMESPACE=
export ADBPG_NAMESPACE_PASSWORD=
```

激活环境变量到终端：

```
source ./adbpg_env.sh
```

## 执行迁移

```sh
cd dify/tools/wea2adb
python main.py
```

当您看到

```
migration successfully.
```

说明迁移已经完成了。