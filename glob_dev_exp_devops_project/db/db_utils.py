"""
Utils to interact with the database
===================================
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, StringConstraints
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base
from typing_extensions import Annotated


SCHEMA_NAME = "mydb"
USER_NAME = "project_user "
PASSWORD = "password"
PORT = 3306
HOST = "127.0.0.1"

# Table schema

Base = declarative_base()


class UsersDataORM(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, nullable=False)
    user_name = Column(String(50), nullable=False)
    creation_date = Column(String(50), nullable=False)


class UsersDataModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    user_name: Annotated[str, StringConstraints(max_length=50)]
    creation_date: Annotated[str, StringConstraints(max_length=50)]
