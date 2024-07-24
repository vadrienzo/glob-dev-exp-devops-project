"""
Utils to interact with the database
===================================
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, StringConstraints
from typing_extensions import Annotated

# Database connection details
DB_SCHEMA_NAME = "mydb"
DB_USER_NAME = "vadiaz"
DB_PASSWORD = "password"
DB_PORT = 3306
DB_HOST = "127.0.0.1"

# Table schema
TABLE_SCHEMAS = {
    "users": {
        "user_id": "INT NOT NULL",
        "user_name": "VARCHAR(50) NOT NULL",
        "creation_date": "VARCHAR(50) NOT NULL",
        "primary_key": "user_id",
    }
}


class UsersDataModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    user_name: Annotated[str, StringConstraints(max_length=50)]
    creation_date: Annotated[str, StringConstraints(max_length=50)]
