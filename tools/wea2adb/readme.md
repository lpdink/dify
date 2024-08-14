# 从weaviate 迁移数据到adbpg

## 构建执行迁移代码的镜像

```sh
cd tools/wea2adb
docker build . -t wea2adb:latest
```

## 拷贝待迁移数据

拷贝您的dify数据到wea2adb目录

```sh
cp -r dify/docker/volumes/ tools/wea2adb/weaviate
```

## 填写adbpg账户配置

打开.env，按照您的信息填写；

```sh
ADBPG_ACCESS_KEY_ID=
ADBPG_ACCESS_KEY_SECRET=
ADBPG_REGION_ID=
ADBPG_INSTANCE_ID=
ADBPG_ACCOUNT=
ADBPG_ACCOUNT_PASSWORD=
ADBPG_NAMESPACE=
ADBPG_NAMESPACE_PASSWORD=
```

## 执行迁移

```sh
cd dify/tools/wea2adb
docker compose up
```

这会启动三个容器：
- 我们刚才构建的迁移主程序，负责数据迁移及pg数据修改
- weaviate数据库，迁移程序读取其中的数据并上传到远程adbpg数据库。
- 本地postgresql数据库，dify将每个文档的向量数据库提供商保存在datasets表的index_struct列，在完成wea2adb的迁移后，更新其类型为adbpg的。

> 具体来说，它执行SQL语句：
```sql
UPDATE datasets
SET index_struct = jsonb_set(index_struct::jsonb, '{type}', '"analyticdb"', false)
WHERE index_struct::jsonb ->> 'type' = 'weaviate';
```

当您看到

```
migration successfully.
update pg datasets successfully.
```

说明迁移已经完成了。

## 写回数据

迁移会修改volumes目录下pg数据库中的信息，这对于存量数据使用adbpg是必不可少的，需要覆盖回dify的volumes。

**注意**: 请务必做好备份

```sh
# 备份
cp -r dify/docker/volumes dify/docker/volumes_bk
# 删除
rm -r dify/docker/volumes/db/data
# 写回
cp -r tools/wea2adb/volumes/db/data dify/docker/volumes/db/data
```