from typing import Optional

from pydantic import BaseModel, Field


class AnalyticdbConfig(BaseModel):
    """
    Analyticdb configs
    """

    ANALYTICDB_KEY_ID : Optional[str] = Field(
        description='Analyticdb key_id',
        default=None,
    )
    ANALYTICDB_KEY_SECRET : Optional[str] = Field(
        description='Analyticdb key_secret',
        default=None,
    )
    ANALYTICDB_REGION_ID : Optional[str] = Field(
        description='Analyticdb region_id',
        default=None,
    )
    ANALYTICDB_INSTANCE_ID : Optional[str] = Field(
        description='Analyticdb instance_id',
        default=None,
    )
    ANALYTICDB_ACCOUNT : Optional[str] = Field(
        description='Analyticdb account',
        default=None,
    )
    ANALYTICDB_PASSWORD : Optional[str] = Field(
        description='Analyticdb password',
        default=None,
    )
    ANALYTICDB_NAMESPACE : Optional[str] = Field(
        description='Analyticdb namespace',
        default=None,
    )
    ANALYTICDB_NAMESPACE_PASSWORD : Optional[str] = Field(
        description='Analyticdb namespace_password',
        default=None,
    )
