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

from pydantic import BaseModel
from typing import Any, Mapping, NamedTuple, Protocol, Sequence


from glob_dev_exp_devops_project.db.db_utils import (
    HOST,
    PASSWORD,
    PORT,
    SCHEMA_NAME,
    USER_NAME,
)

FilteredData = NamedTuple(
    "FilteredData", [("data", dict[str, Any]), ("where", str), ("query", str)]
)

_CoreSingleExecuteParams = Mapping[str, Any]
_CoreMultiExecuteParams = Sequence[_CoreSingleExecuteParams]
_DBAPICursorDescription = Sequence[Any] | _CoreSingleExecuteParams
_DBAPIMultiExecuteParams = Sequence[Sequence[Any]] | _CoreMultiExecuteParams
_DBAPISingleExecuteParams = Sequence[Any] | _CoreSingleExecuteParams


def get_connection():
    """
    Get a connection to the database

    Returns:
        The connection to the database
    """
    return pymysql.connect(
        host=HOST, port=PORT, user=USER_NAME, passwd=PASSWORD, db=SCHEMA_NAME
    )


class DBAPICursor(Protocol):
    """protocol representing a :pep:`249` database cursor.

    .. versionadded:: 2.0

    .. seealso::

        `Cursor Objects <https://www.python.org/dev/peps/pep-0249/#cursor-objects>`_
        - in :pep:`249`

    """  # noqa: E501

    @property
    def description(
        self,
    ) -> _DBAPICursorDescription:
        """The description attribute of the Cursor.

        .. seealso::

            `cursor.description <https://www.python.org/dev/peps/pep-0249/#description>`_
            - in :pep:`249`


        """  # noqa: E501
        ...

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
