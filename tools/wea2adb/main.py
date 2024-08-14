import os
from weaviate2adbpg import WeaviateVector, WeaviateConfig
from adbpg import AnalyticdbConfig, AnalyticdbVector, build_documents

WEAVIATE_ENDPOINT = os.environ.get("WEAVIATE_ENDPOINT")
WEAVIATE_API_KEY = os.environ.get("WEAVIATE_API_KEY")
DB_USERNAME = os.environ.get("DB_USERNAME")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT")
DB_DATABASE = os.environ.get("DB_DATABASE")

# adbpg配置
ADBPG_ACCESS_KEY_ID = os.environ.get("ADBPG_ACCESS_KEY_ID")
ADBPG_ACCESS_KEY_SECRET = os.environ.get("ADBPG_ACCESS_KEY_SECRET")
ADBPG_REGION_ID = os.environ.get("ADBPG_REGION_ID")
ADBPG_INSTANCE_ID = os.environ.get("ADBPG_INSTANCE_ID")
ADBPG_ACCOUNT = os.environ.get("ADBPG_ACCOUNT")
ADBPG_ACCOUNT_PASSWORD = os.environ.get("ADBPG_ACCOUNT_PASSWORD")
ADBPG_NAMESPACE = os.environ.get("ADBPG_NAMESPACE")
ADBPG_NAMESPACE_PASSWORD = os.environ.get("ADBPG_NAMESPACE_PASSWORD")

"""
在创建集合前，是否首先删除adbpg中的重名集合
    - 这些集合名类似于：Vector_index_74d59845_ea24_497b_aaf3_5383b9939bac_Node
    - 数据迁移脚本仅应该在weaviate迁移到adbpg时使用，这意味着应该由迁移脚本，根据本地weaviate的集合名创建adbpg中的集合名。
    - 只有在脚本执行因为网络等原因中断，导致集合创建，但是数据没有完整插入时使用，会删除掉adbpg中，与本地weaviate集合重名的数据集合。
    - 警告：如果要修改为True，请确保理解你在做什么，以免造成数据误删除。
"""
ADBPG_DELETE_REMOTE_DUPLICATE_COLLECTION = os.environ.get("ADBPG_DELETE_REMOTE_DUPLICATE_COLLECTION", False)

def init_weaviate():
    config = WeaviateConfig(endpoint=WEAVIATE_ENDPOINT, api_key=WEAVIATE_API_KEY)
    try:
        vec = WeaviateVector(config)
    except ConnectionError:
        raise ConnectionError("weaviate service not alive, please call `docker compose up` at first.")
    assert vec._client.is_live(), "weaviate service not alive, please call `docker compose up` at first."
    return vec

def init_adbpg():
    assert ADBPG_ACCESS_KEY_ID is not None, "expected to set adbpg account info, please config and source `adbpg_env.sh` "
    config = AnalyticdbConfig(access_key_id=ADBPG_ACCESS_KEY_ID, access_key_secret=ADBPG_ACCESS_KEY_SECRET, region_id=ADBPG_REGION_ID, instance_id=ADBPG_INSTANCE_ID, account=ADBPG_ACCOUNT, account_password=ADBPG_ACCOUNT_PASSWORD, namespace=ADBPG_NAMESPACE, namespace_password=ADBPG_NAMESPACE_PASSWORD)
    return AnalyticdbVector(config)

def update_pg_datasets():
    import psycopg2

    conn_params = {
        'dbname': DB_DATABASE,
        'user': DB_USERNAME,
        'password': DB_PASSWORD,
        'host': DB_HOST,
        'port': DB_PORT,
    }

    try:
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        update_query = """
        UPDATE datasets
        SET index_struct = jsonb_set(index_struct::jsonb, '{type}', '"analyticdb"', false)
        WHERE index_struct::jsonb ->> 'type' = 'weaviate';
        """

        cursor.execute(update_query)
        conn.commit()

        print("update pg datasets successfully.")

    except Exception as e:
        print(f"An error occurred: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def _split_batch(data_list, batch_size=30):
    return [data_list[i:i + batch_size] for i in range(0, len(data_list), batch_size)]

def main():
    weaviate = init_weaviate()
    adbpg = init_adbpg()
    ori_collections = weaviate.list_collection()
    collection_idx = 1
    if len(ori_collections)==0:
        print("local weaviate database is empty, nothing to migrate. Make sure copy dify/docker/volumes/weaviate to dify/tools/wea2adb/ .")
        exit()
    for collection in ori_collections:
        # adbpg不允许collection_name带有大写字母
        # 这不会带来rds的迁移问题，因为在检索时，collection_name也会被lower，参见https://github.com/langgenius/dify/blob/main/api/core/rag/datasource/vdb/analyticdb/analyticdb_vector.py#L51
        collection = collection.lower()
        if ADBPG_DELETE_REMOTE_DUPLICATE_COLLECTION:
            print(f"delete remote collection:{collection}")
            adbpg.delete(collection)
        print(f"upload collection:{collection}, {collection_idx} in {len(ori_collections)}")
        data = weaviate.get_collection_data(collection)
        documents = build_documents(data)
        adbpg.create_collection(collection, len(documents[0].vector))
        batches = _split_batch(documents, 30)
        batch_idx = 1
        for batch in batches:
            print(f"upload batch, {batch_idx} in {len(batches)}")
            batch_idx+=1
            adbpg.add_texts(collection, batch)
        collection_idx+=1
    print("migration successfully.")
    update_pg_datasets()

if __name__=="__main__":
    main()