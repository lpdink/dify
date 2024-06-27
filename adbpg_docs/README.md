# 使用adbpg for dify

## 配置adbpg为向量数据库

克隆本项目，切换到本分支：

```sh
git clone https://github.com/lpdink/dify.git -b use_adbpg
```

填写您的向量数据库aksk：  
打开dify/docker/docker-compose.yaml，搜索CHANGE_HERE，按照您的信息，修改以下字段：

```yaml
ANALYTICDB_KEY_ID: CHANGE_HERE
ANALYTICDB_KEY_SECRET: CHANGE_HERE
ANALYTICDB_REGION_ID: CHANGE_HERE
ANALYTICDB_INSTANCE_ID: CHANGE_HERE
ANALYTICDB_ACCOUNT: CHANGE_HERE
ANALYTICDB_PASSWORD: CHANGE_HERE
ANALYTICDB_NAMESPACE: CHANGE_HERE
ANALYTICDB_NAMESPACE_PASSWORD: CHANGE_HERE
```

注意，在service/api/environment和service/worker/environment下有两处这样的字段，保证都做修改。

由于dify暂时没有合并进adbpg，并构建新的镜像，我们需要自己构建镜像，使用以下命令构建镜像：

```sh
cd dify
docker build -t langgenius/dify-api:latest .
```

## 配置adbpg为PG数据库

dify使用本地PG数据库来保存历史文档等信息，难以持续提供高可用的服务，推荐使用adbpg替换本地的临时pg数据库。

打开dify/docker/docker-compose.yaml，按照您的信息更改以下字段：

```yaml
DB_USERNAME: CHANGE_HERE
DB_PASSWORD: CHANGE_HERE
DB_HOST: CHANGE_HERE
DB_PORT: 5432
DB_DATABASE: CHANGE_HERE
```

同样的，注意在service/api/environment和service/worker/environment下有两处这样的字段，保证都做修改。  

接下来，我们需要按照dify的业务要求，更新PG数据库表，这会用到flask 
migrate，因此需要我们在宿主机上安装dify要求的环境，以便能导入flask app:

您需要安装poetry，之后在python 3.10.x下执行：

```sh
cd dify/api
poetry install --sync --no-cache 
```

接下来，我们在环境变量中写入连接到adbpg数据库的信息，打开dify/adbpg_docs/pg.env.sh，更改字段为您的数据库信息：

```sh
export DB_USERNAME=CHANGE_HERE
export DB_PASSWORD=CHANGE_HERE
export DB_HOST=CHANGE_HERE
export DB_PORT=5432
export DB_DATABASE=CHANGE_HERE
```

激活环境变量到您的终端：

```sh
source dify/adbpg_docs/pg.env.sh
```

接下来，我们更新数据库表，依次执行：

```sh
cd dify/api
flask db stamp head
flask db migrate
flask db upgrade
```

至此，数据库表更新完毕，您访问adbpg的数据库终端，应当看到您的数据库被创建了一系列dify的表。

## 启动服务

至此，我们完成了配置，可以启动服务：

```sh
cd dify/docker
docker compose up -d
```