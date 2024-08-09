from pydantic import BaseModel, model_validator
from typing import Any, Optional
import weaviate
import requests

class WeaviateConfig(BaseModel):
    endpoint: str
    api_key: Optional[str] = None
    batch_size: int = 100

    @model_validator(mode='before')
    def validate_config(cls, values: dict) -> dict:
        if not values['endpoint']:
            raise ValueError("config WEAVIATE_ENDPOINT is required")
        return values
    
class WeaviateVector:
    def __init__(self, config:WeaviateConfig) -> None:
        self._client = self._init_client(config)

    def _init_client(self, config: WeaviateConfig) -> weaviate.Client:
        auth_config = weaviate.auth.AuthApiKey(api_key=config.api_key)

        weaviate.connect.connection.has_grpc = False

        try:
            client = weaviate.Client(
                url=config.endpoint,
                auth_client_secret=auth_config,
                timeout_config=(5, 60),
                startup_period=None
            )
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Vector database connection error")

        client.batch.configure(
            # `batch_size` takes an `int` value to enable auto-batching
            # (`None` is used for manual batching)
            batch_size=config.batch_size,
            # dynamically update the `batch_size` based on import speed
            dynamic=True,
            # `timeout_retries` takes an `int` value to retry on time outs
            timeout_retries=3,
        )

        return client
    
    def list_collection(self):
        return [collection['class'] for collection in self._client.schema.get()["classes"]]

    def get_collection_data(self, collection_name):
        rows = self._client.data_object.get(class_name=collection_name,with_vector=True)["objects"]
        ret = []
        for row in rows:
            dic = {}
            dic["id"] = row["id"]
            dic["metadata"] = row["properties"]
            dic["vector"] = row["vector"]
            ret.append(dic)
        return ret