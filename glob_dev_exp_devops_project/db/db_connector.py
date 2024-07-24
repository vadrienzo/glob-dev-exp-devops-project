"""
Database connector module
=========================

1. Use (any) remote MySQLservice.

2. The REST API (Please refer to REST API section) will read and write data
using a MySQL table called users:
    . users table will have 3 columns:
        - user_id: primary key, int, not null
        - user_name: varchar50],not null
        - creation_date: varchar[50] which will store user creation date
        (in any format):
            For example:
        | user_id | user_name |   creation_date     |
        |---------|-----------|---------------------|
        | 1       | user1     | 2021-01-01 00:00:00 |
        | 2       | user2     | 2021-01-02 00:00:00 |

3. Table can be created manually (and not from code)

"""

from __future__ import annotations

import pymysql

from flask import Response, abort, jsonify
from pydantic import BaseModel
from pydantic_core import ValidationError
from pymysqlpool import ConnectionPool
from typing import Any, Literal, Mapping, NamedTuple, Protocol, Sequence

from glob_dev_exp_devops_project.db.db_utils import (
    DB_HOST,
    DB_PASSWORD,
    DB_PORT,
    DB_SCHEMA_NAME,
    DB_USER_NAME,
    TABLE_SCHEMAS,
    UsersDataModel,
)
from glob_dev_exp_devops_project.exceptions import DBFailureReasonsEnum

# creating a pool of database connections
mypool = ConnectionPool(
    name="mypool",
    host=DB_HOST,
    user=DB_USER_NAME,
    password=DB_PASSWORD,
    port=DB_PORT,
    db=DB_SCHEMA_NAME,
    con_lifetime=600,
    maxsize=10,
    size=5,
    autocommit=True,
    charset="utf8mb4",
)


def get_connection() -> pymysql.Connection:
    return mypool.get_connection()


FilteredData = NamedTuple(
    "FilteredData", [("data", dict[str, Any]), ("where", str), ("query", str)]
)

_CoreSingleExecuteParams = Mapping[str, Any]
_CoreMultiExecuteParams = Sequence[_CoreSingleExecuteParams]
_DBAPICursorDescription = Sequence[Any] | _CoreSingleExecuteParams
_DBAPIMultiExecuteParams = Sequence[Sequence[Any]] | _CoreMultiExecuteParams
_DBAPISingleExecuteParams = Sequence[Any] | _CoreSingleExecuteParams


class DBAPICursor(Protocol):
    """protocol representing a :pep:`249` database cursor.

    `Cursor Objects <https://www.python.org/dev/peps/pep-0249/#cursor-objects>`_
    - in :pep:`249`

    """  # noqa: E501

    @property
    def description(
        self,
    ) -> _DBAPICursorDescription: ...

    @property
    def rowcount(self) -> int: ...

    arraysize: int

    lastrowid: int

    def close(self) -> None: ...

    def execute(
        self,
        operation: Any,
        parameters: _DBAPISingleExecuteParams | None = None,
    ) -> Any: ...

    def executemany(
        self,
        operation: Any,
        parameters: _DBAPIMultiExecuteParams,
    ) -> Any: ...

    def fetchone(self) -> Any | None: ...

    def fetchmany(self, size: int = ...) -> Sequence[Any]: ...

    def fetchall(self) -> Sequence[Any]: ...

    def setinputsizes(self, sizes: Sequence[Any]) -> None: ...

    def setoutputsize(self, size: Any, column: Any) -> None: ...

    def callproc(
        self, procname: str, parameters: Sequence[Any] = ...
    ) -> Any: ...

    def nextset(self) -> bool | None: ...

    def __getattr__(self, key: str) -> Any: ...


class ORM:
    """
    Object Relational Mapper to interact with the database
    """

    def __init__(self, db_cursor: DBAPICursor, table_name: str | None = None):
        self.db_cursor = db_cursor
        self.table_name = table_name

    def create_table(
        self, schema_name: str, table_name: str, table_schema: dict[str, str]
    ):
        """
        Create a table in the corresponding database.
        This table must have a primary key

        Args:
            db_cursor: Cursor object to execute the query
            schema_name: The name of the schema
            table_name: The name of the table
            table_schema: The schema of the table

        """
        if not all(isinstance(v, str) for v in table_schema.values()):
            raise ValueError("All schema value should be a string")

        if "primary_key" not in table_schema:
            raise KeyError("Schema should contain a primary_key")

        primary_key = f"PRIMARY KEY (`{table_schema['primary_key']}`)"
        schema = ", ".join(
            f"`{k}` {v}" for k, v in table_schema.items() if k != "primary_key"
        )

        self.db_cursor.execute(
            f"CREATE TABLE `{schema_name}`.`{table_name}`({schema}, {primary_key});"
        )

    def query(self, query: str):
        """
        Execute a query in the database

        Args:
            query: The query to be executed
        """
        self.db_cursor.execute(query)
        return self.db_cursor.fetchall()

    def insert(self, table_name: str | None = None, **kwargs):
        """
        Insert a row into the table. The keys of the kwargs should be the column
        names and the values should be the values to be inserted.

        Args:
            table_name: The name of the table
            kwargs: The columns and values to be inserted
        """
        table_name = table_name or self.table_name
        columns = ", ".join(f"`{k}`" for k in kwargs.keys())
        values = ", ".join(f"'{v}'" for v in kwargs.values())

        self.db_cursor.execute(
            f"INSERT INTO `{table_name}` ({columns}) VALUES ({values});"
        )

    def select(
        self,
        table_name: str | None = None,
        columns: list[str] | None = None,
        where: str = "",
    ):
        """
        Select the columns from the table. If where is provided, it will be used
        as a condition.

        Args:
            table_name: The name of the table, if None, the table_name from the
                        ORM object will be used
            columns: The columns to be selected, if None, all columns will be
                     selected
            where: The condition to be used in the query, default is ""
        """
        table_name = table_name or self.table_name
        str_columns = (
            ", ".join(f"`{c}`" for c in columns)
            if columns is not None
            else "*"
        )
        query = f"SELECT {str_columns} FROM `{table_name}`"
        if where:
            query += f" WHERE {where}"
        self.db_cursor.execute(query)
        return self.db_cursor.fetchall()

    def update(self, where: str, table_name: str | None = None, **kwargs):
        """
        Update the table with the values provided in kwargs. The where clause
        is used to filter the rows to be updated. The keys of the kwargs should
        be the column names and the values should be the values to be updated.

        Args:
            where: The condition to be used in the query
            table_name: The name of the table, if None, the table_name from the
                        ORM object will be used
            kwargs: The columns and values to be updated
        """
        table_name = table_name or self.table_name
        set_values = ", ".join(f"`{k}` = '{v}'" for k, v in kwargs.items())
        self.db_cursor.execute(
            f"UPDATE `{table_name}` SET {set_values} WHERE {where};"
        )

    def delete(self, where: str, table_name: str | None = None):
        """
        Delete the rows from the table. The where clause is used to filter the
        rows to be deleted.

        Args:
            where: The condition to be used in the query
            table_name: The name of the table, if None, the table_name from the
                        ORM object will be used
        """
        table_name = table_name or self.table_name
        self.db_cursor.execute(f"DELETE FROM `{table_name}` WHERE {where};")

    def get_table_columns_info(
        self, table_name: str | None = None
    ) -> Sequence[Any]:
        """
        Get the columns information from the table

        Args:
            table_name: The name of the table, if None, the table_name from the
                        ORM object will be used

        Returns:
            The columns information from the table, e.g.
                (name, type, null, key, default, extra)
        """
        table_name = table_name or self.table_name
        self.db_cursor.execute(f"SHOW COLUMNS FROM `{table_name}`;")

        return self.db_cursor.fetchall()

    def get_table_columns(self, table_name: str | None = None) -> list[str]:
        """
        Get the columns from the table

        Args:
            table_name: The name of the table, if None, the table_name from the
                        ORM object will be used

        Returns:
            The columns from the table
        """
        table_name = table_name or self.table_name
        return [
            column[0] for column in self.get_table_columns_info(table_name)
        ]

    def get_table_as_json(
        self, table_name: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Get the data from the table as a json

        Args:
            table_name: The name of the table, if None, the table_name from the
                        ORM object will be used

        Returns:
            The data from the table as a json
        """
        table_name = table_name or self.table_name
        return [
            dict(zip(self.get_table_columns(table_name), row))
            for row in self.select(table_name)
        ]

    def validate_processed_data(
        self,
        validation_model: type[BaseModel],
        fetched_data: Sequence[Sequence[Any]],
        table_name: str | None = None,
    ) -> list[Any]:
        """
        Process the fetched data from the database as a json

        Args:
            validation_model: The model to validate the data
            fetched_data: The data fetched from the database
            table_name: The name of the table, if None, the table_name from the
                        ORM object will be used

        Returns:
            The fetched data processed as a pydanctic model
        """
        table_name = table_name or self.table_name
        columns = self.get_table_columns(table_name)
        return [
            validation_model.model_validate(dict(zip(columns, row)))
            for row in fetched_data
        ]


def add_user_data(
    db_connection: pymysql.Connection,
    user_id: int,
    new_user_data: UsersDataModel,
    table_name: str = "users",
) -> tuple[Response, Literal[500] | Literal[200]]:
    """
    Add the user data to the database. If the user_id already exists, it will
    return an error message.

    Args:
        db_connection: The database connection.
        user_id: The user id.
        new_user_data: The user data to be added.
        table_name: The name of the table.

    Returns:
        Depending on the success or failure of the operation, it will return
        a JSON response with the status and the user added or an error message.
    """
    with db_connection as db_conn:
        my_db = ORM(db_cursor=db_conn.cursor(), table_name=table_name)
        # check if the user_id already exists
        fetched_user_data = my_db.select(
            columns=["user_id"],
            where=f"user_id = {user_id}",
        )
        # if the user_id already exists, return an error
        if fetched_user_data:
            return abort(500, DBFailureReasonsEnum.ID_ALREADY_EXISTS)
        # insert the new user
        my_db.insert(**new_user_data.model_dump())
    return (
        jsonify({"status": "ok", "user_added": new_user_data.user_id}),
        200,
    )


def get_user_from_database(
    db_connection: pymysql.Connection, user_id: int
) -> tuple[Response, Literal[500] | Literal[200] | Literal[422]]:
    """
    Get the user name from the database.

    Args:
        db_connection: The database connection.
        user_id: The user id.

    Returns:
        Depending on the success or failure of the operation, it will return
        a JSON response with the status and the user name or an error message.
    """
    with db_connection as db_conn:
        my_db = ORM(db_cursor=db_conn.cursor(), table_name="users")
        fetched_user_data = my_db.select(where=f"user_id = {user_id}")
        # if the fetched data is empty, return an error
        if not fetched_user_data:
            return abort(500, DBFailureReasonsEnum.NO_SUCH_ID)
        if len(fetched_user_data) > 1:
            # this should never happen
            raise ValueError(f"More than one user with the same id: {user_id}")

        # process the fetched data as json and get the user name
        try:
            processed_data: UsersDataModel = my_db.validate_processed_data(
                validation_model=UsersDataModel, fetched_data=fetched_user_data
            ).pop()
        except ValidationError as e:
            return abort(422, str(e))
    return (
        jsonify(
            {
                "status": "ok",
                **processed_data.model_dump(),
            }
        ),
        200,
    )


def update_user_data(
    db_connection: pymysql.Connection,
    user_id: int,
    validated_data: UsersDataModel,
) -> tuple[Response, Literal[500]] | tuple[Response, Literal[200]]:
    """
    Update the user name in the database.

    Args:
        db_connection: The database connection.
        user_id: The user id.
        validated_data: The user data.

    Returns:
        Depending on the success or failure of the operation, it will return
        a JSON response with the status and the user updated or an error message.
    """
    with db_connection as db_conn:
        my_db = ORM(db_cursor=db_conn.cursor(), table_name="users")
        fetched_user_data = my_db.select(
            columns=["user_name"], where=f"user_id = {user_id}"
        )
        if not fetched_user_data:
            return abort(500, DBFailureReasonsEnum.NO_SUCH_ID)
        my_db.update(
            where=f"user_id = {user_id}", **validated_data.model_dump()
        )

    return (
        jsonify({"status": "ok", "user_updated": validated_data.user_id}),
        200,
    )


def delete_user_data(
    db_connection: pymysql.Connection, user_id: int
) -> tuple[Response, Literal[500]] | tuple[Response, Literal[200]]:
    """
    Delete the user from the database.

    Args:
        db_connection: The database connection.
        user_id: The user id.

    Returns:
        Depending on the success or failure of the operation, it will return
        a JSON response with the status and the user deleted or an error message.
    """
    with db_connection as db_conn:
        my_db = ORM(db_cursor=db_conn.cursor(), table_name="users")
        fetched_user_data = my_db.select(
            columns=["user_name"], where=f"user_id = {user_id}"
        )
        if not fetched_user_data:
            return abort(500, DBFailureReasonsEnum.NO_SUCH_ID)
        my_db.delete(where=f"user_id = {user_id}")

    return jsonify({"status": "ok", "user_deleted": user_id}), 200


def create_table(
    db_connection: pymysql.Connection,
    table_name: str,
    schema_name: str = DB_SCHEMA_NAME,
    table_schemas: dict[str, Any] | None = None,
) -> None:
    """
    Create a table in the corresponding database.
    This table must have a primary key

    Args:
        db_connection: The database connection.
        table_name: The name of the table.
        schema_name: The name of the schema.

    """
    table_schemas = table_schemas or TABLE_SCHEMAS
    if table_name not in table_schemas:
        raise ValueError(f"Table schema for {table_name} not found")
    with db_connection as db_conn:
        my_db = ORM(db_cursor=db_conn.cursor(), table_name=table_name)
        # check if there is such table
        try:
            my_db.get_table_columns_info()
        except pymysql.err.ProgrammingError:
            my_db.create_table(
                schema_name=schema_name,
                table_name=table_name,
                table_schema=table_schemas[table_name],
            )
