import json
from typing import Any

from pydantic import BaseModel

_import_err_msg = (
    "`alibabacloud_gpdb20160503` and `alibabacloud_tea_openapi` packages not found, "
    "please run `pip install alibabacloud_gpdb20160503 alibabacloud_tea_openapi`"
)


from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any, Optional

from pydantic import BaseModel, Field


class Document(BaseModel):
    """Class for storing a piece of text and associated metadata."""

    page_content: str

    vector: Optional[list[float]] = None

    """Arbitrary metadata about the page content (e.g., source, relationships to other
        documents, etc.).
    """
    metadata: Optional[dict] = Field(default_factory=dict)

def build_documents(records)->list[Document]:
    ans = []
    for record in records:
        doc = Document(
            page_content=record['metadata']['text'],
            vector=record['vector'],
            metadata=record['metadata']
        )
        ans.append(doc)
    return ans

class AnalyticdbConfig(BaseModel):
    access_key_id: str
    access_key_secret: str
    region_id: str
    instance_id: str
    account: str
    account_password: str
    namespace: str = ("dify",)
    namespace_password: str = (None,)
    metrics: str = ("cosine",)
    read_timeout: int = 60000
    def to_analyticdb_client_params(self):
        return {
            "access_key_id": self.access_key_id,
            "access_key_secret": self.access_key_secret,
            "region_id": self.region_id,
            "read_timeout": self.read_timeout,
        }

class AnalyticdbVector:
    def __init__(self, config: AnalyticdbConfig):
        # collection_name must be updated every time
        try:
            from alibabacloud_gpdb20160503.client import Client
            from alibabacloud_tea_openapi import models as open_api_models
        except:
            raise ImportError(_import_err_msg)
        self.config = config
        self._client_config = open_api_models.Config(
            user_agent="dify", **config.to_analyticdb_client_params()
        )
        self._client = Client(self._client_config)
        self._initialize()
        AnalyticdbVector._init = True

    def _initialize(self) -> None:
        self._initialize_vector_database()
        self._create_namespace_if_not_exists()

    def _initialize_vector_database(self) -> None:
        from alibabacloud_gpdb20160503 import models as gpdb_20160503_models
        request = gpdb_20160503_models.InitVectorDatabaseRequest(
            dbinstance_id=self.config.instance_id,
            region_id=self.config.region_id,
            manager_account=self.config.account,
            manager_account_password=self.config.account_password,
        )
        self._client.init_vector_database(request)

    def _create_namespace_if_not_exists(self) -> None:
        from alibabacloud_gpdb20160503 import models as gpdb_20160503_models
        from Tea.exceptions import TeaException
        try:
            request = gpdb_20160503_models.DescribeNamespaceRequest(
                dbinstance_id=self.config.instance_id,
                region_id=self.config.region_id,
                namespace=self.config.namespace,
                manager_account=self.config.account,
                manager_account_password=self.config.account_password,
            )
            self._client.describe_namespace(request)
        except TeaException as e:
            if e.statusCode == 404:
                request = gpdb_20160503_models.CreateNamespaceRequest(
                    dbinstance_id=self.config.instance_id,
                    region_id=self.config.region_id,
                    manager_account=self.config.account,
                    manager_account_password=self.config.account_password,
                    namespace=self.config.namespace,
                    namespace_password=self.config.namespace_password,
                )
                self._client.create_namespace(request)
            else:
                raise ValueError(
                    f"failed to create namespace {self.config.namespace}: {e}"
                )
            
    def create_collection(self, collection_name, embedding_dimension):
        from alibabacloud_gpdb20160503 import models as gpdb_20160503_models
        from Tea.exceptions import TeaException
        # Collection.AlreadyExists
        metadata = '{"ref_doc_id":"text","page_content":"text","metadata_":"jsonb"}'
        full_text_retrieval_fields = "page_content"
        request = gpdb_20160503_models.CreateCollectionRequest(
            dbinstance_id=self.config.instance_id,
            region_id=self.config.region_id,
            manager_account=self.config.account,
            manager_account_password=self.config.account_password,
            namespace=self.config.namespace,
            collection=collection_name,
            dimension=embedding_dimension,
            metrics=self.config.metrics,
            metadata=metadata,
            full_text_retrieval_fields=full_text_retrieval_fields,
        )
        try:
            self._client.create_collection(request)
        except TeaException as e:
            if "Collection.AlreadyExists" in e.code:
                raise RuntimeError(f"Collection {collection_name} AlreadyExists, only use the script in weaviate to adbpg migration. If it's caused by upsert failed, set ADBPG_DELETE_REMOTE_DUPLICATE_COLLECTION=True to delete remote duplicate collection. MAKE SURE YOU KNOW WHAR YOU ARE DOING.")
            else:
                raise RuntimeError(e)

    def _create_collection_if_not_exists(self, collection_name, embedding_dimension: int):
        from alibabacloud_gpdb20160503 import models as gpdb_20160503_models
        from Tea.exceptions import TeaException
        try:
            request = gpdb_20160503_models.DescribeCollectionRequest(
                dbinstance_id=self.config.instance_id,
                region_id=self.config.region_id,
                namespace=self.config.namespace,
                namespace_password=self.config.namespace_password,
                collection=collection_name,
            )
            self._client.describe_collection(request)
        except TeaException as e:
            if e.statusCode == 404:
                metadata = '{"ref_doc_id":"text","page_content":"text","metadata_":"jsonb"}'
                full_text_retrieval_fields = "page_content"
                request = gpdb_20160503_models.CreateCollectionRequest(
                    dbinstance_id=self.config.instance_id,
                    region_id=self.config.region_id,
                    manager_account=self.config.account,
                    manager_account_password=self.config.account_password,
                    namespace=self.config.namespace,
                    collection=collection_name,
                    dimension=embedding_dimension,
                    metrics=self.config.metrics,
                    metadata=metadata,
                    full_text_retrieval_fields=full_text_retrieval_fields,
                )
                self._client.create_collection(request)
            else:
                raise ValueError(
                    f"failed to create collection {collection_name}: {e}"
                )

    def create(self, collection_name, texts: list[Document]):
        dimension = len(texts[0].vector)
        self._create_collection_if_not_exists(collection_name, dimension)
        self.add_texts(texts)

    def add_texts(
        self, collection_name, documents: list[Document]
    ):
        from alibabacloud_gpdb20160503 import models as gpdb_20160503_models
        rows: list[gpdb_20160503_models.UpsertCollectionDataRequestRows] = []
        for doc in documents:
            metadata = {
                "ref_doc_id": doc.metadata["doc_id"],
                "page_content": doc.page_content,
                "metadata_": json.dumps(doc.metadata),
            }
            rows.append(
                gpdb_20160503_models.UpsertCollectionDataRequestRows(
                    vector=doc.vector,
                    metadata=metadata,
                )
            )
        request = gpdb_20160503_models.UpsertCollectionDataRequest(
            dbinstance_id=self.config.instance_id,
            region_id=self.config.region_id,
            namespace=self.config.namespace,
            namespace_password=self.config.namespace_password,
            collection=collection_name,
            rows=rows,
        )
        self._client.upsert_collection_data(request)

    def text_exists(self, collection_name, id: str) -> bool:
        from alibabacloud_gpdb20160503 import models as gpdb_20160503_models
        request = gpdb_20160503_models.QueryCollectionDataRequest(
            dbinstance_id=self.config.instance_id,
            region_id=self.config.region_id,
            namespace=self.config.namespace,
            namespace_password=self.config.namespace_password,
            collection=collection_name,
            metrics=self.config.metrics,
            include_values=True,
            vector=None,
            content=None,
            top_k=1,
            filter=f"ref_doc_id='{id}'"
        )
        response = self._client.query_collection_data(request)
        return len(response.body.matches.match) > 0

    def delete_by_ids(self, collection_name, ids: list[str]) -> None:
        from alibabacloud_gpdb20160503 import models as gpdb_20160503_models
        ids_str = ",".join(f"'{id}'" for id in ids)
        ids_str = f"({ids_str})"
        request = gpdb_20160503_models.DeleteCollectionDataRequest(
            dbinstance_id=self.config.instance_id,
            region_id=self.config.region_id,
            namespace=self.config.namespace,
            namespace_password=self.config.namespace_password,
            collection=collection_name,
            collection_data=None,
            collection_data_filter=f"ref_doc_id IN {ids_str}",
        )
        self._client.delete_collection_data(request)

    def search_by_vector(
        self, collection_name, query_vector: list[float], **kwargs: Any
    ) -> list[Document]:
        from alibabacloud_gpdb20160503 import models as gpdb_20160503_models
        score_threshold = (
            kwargs.get("score_threshold", 0.0)
            if kwargs.get("score_threshold", 0.0)
            else 0.0
        )
        request = gpdb_20160503_models.QueryCollectionDataRequest(
            dbinstance_id=self.config.instance_id,
            region_id=self.config.region_id,
            namespace=self.config.namespace,
            namespace_password=self.config.namespace_password,
            collection=collection_name,
            include_values=kwargs.pop("include_values", True),
            metrics=self.config.metrics,
            vector=query_vector,
            content=None,
            top_k=kwargs.get("top_k", 4),
            filter=None,
        )
        response = self._client.query_collection_data(request)
        documents = []
        for match in response.body.matches.match:
            if match.score > score_threshold:
                doc = Document(
                    page_content=match.metadata.get("page_content"),
                    metadata=json.loads(match.metadata.get("metadata_")),
                )
                documents.append(doc)
        return documents

    def search_by_full_text(self, collection_name, query: str, **kwargs: Any) -> list[Document]:
        from alibabacloud_gpdb20160503 import models as gpdb_20160503_models
        score_threshold = (
            kwargs.get("score_threshold", 0.0)
            if kwargs.get("score_threshold", 0.0)
            else 0.0
        )
        request = gpdb_20160503_models.QueryCollectionDataRequest(
            dbinstance_id=self.config.instance_id,
            region_id=self.config.region_id,
            namespace=self.config.namespace,
            namespace_password=self.config.namespace_password,
            collection=collection_name,
            include_values=kwargs.pop("include_values", True),
            metrics=self.config.metrics,
            vector=None,
            content=query,
            top_k=kwargs.get("top_k", 4),
            filter=None,
        )
        response = self._client.query_collection_data(request)
        documents = []
        for match in response.body.matches.match:
            if match.score > score_threshold:
                metadata = json.loads(match.metadata.get("metadata_"))
                doc = Document(
                    page_content=match.metadata.get("page_content"),
                    vector=match.metadata.get("vector"),
                    metadata=metadata,
                )
                documents.append(doc)
        return documents

    def delete(self, collection_name) -> None:
        try:
            from alibabacloud_gpdb20160503 import models as gpdb_20160503_models
            request = gpdb_20160503_models.DeleteCollectionRequest(
                collection=collection_name,
                dbinstance_id=self.config.instance_id,
                namespace=self.config.namespace,
                namespace_password=self.config.namespace_password,
                region_id=self.config.region_id,
            )
            self._client.delete_collection(request)
        except Exception as e:
            raise e