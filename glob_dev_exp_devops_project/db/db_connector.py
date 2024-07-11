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

from typing import Any, NamedTuple
from pymysql.cursors import Cursor

from glob_dev_exp_devops_project.db.db_utils import (
    HOST,
    PASSWORD,
    PORT,
    SCHEMA_NAME,
    TABLES_AND_TABLE_SCHEMAS,
    USER_NAME,
)

FilteredData = NamedTuple(
    "FilteredData", [("data", dict[str, Any]), ("where", str), ("query", str)]
)


def create_table():
    # Establishing a connection to DB
    with pymysql.connect(
        host=HOST,
        port=PORT,
        user=USER_NAME,
        passwd=PASSWORD,
        db=SCHEMA_NAME,
    ) as db_conn:
        my_db = ORM(db_cursor=db_conn.cursor(), auto_commit=True)
        # Creating a table
        for table_name, table_schema in TABLES_AND_TABLE_SCHEMAS.items():
            # Creating table
            try:
                my_db.create_table(
                    schema_name=SCHEMA_NAME,
                    table_name=table_name,
                    table_schema=table_schema,
                )
                print(f"Table {table_name} created successfully")
            except pymysql.err.OperationalError:
                print(f"Table {table_name} already exists")


class ORM:
    """
    Object Relational Mapper to interact with the database
    """

    def __init__(self, db_cursor: Cursor, auto_commit: bool = False):
        self.db_cursor = db_cursor
        self.db_cursor.connection.autocommit(auto_commit)

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

    def insert(self, table_name: str, **kwargs):
        """
        Insert a row into the table. The keys of the kwargs should be the column
        names and the values should be the values to be inserted.

        Args:
            table_name: The name of the table
            kwargs: The columns and values to be inserted
        """
        columns = ", ".join(f"`{k}`" for k in kwargs.keys())
        values = ", ".join(f"'{v}'" for v in kwargs.values())

        self.db_cursor.execute(
            f"INSERT INTO `{table_name}` ({columns}) VALUES ({values});"
        )

    def select(
        self,
        table_name: str,
        columns: list[str] | None = None,
        where: str = "",
    ):
        """
        Select the columns from the table. If where is provided, it will be used
        as a condition.

        Args:
            table_name: The name of the table
            columns: The columns to be selected
            where: The condition to be used in the query
        """
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

    def update(self, table_name: str, where: str, **kwargs):
        """
        Update the table with the values provided in kwargs. The where clause
        is used to filter the rows to be updated. The keys of the kwargs should
        be the column names and the values should be the values to be updated.

        Args:
            table_name: The name of the table
            where: The condition to be used in the query
            kwargs: The columns and values to be updated
        """
        set_values = ", ".join(f"`{k}` = '{v}'" for k, v in kwargs.items())
        self.db_cursor.execute(
            f"UPDATE `{table_name}` SET {set_values} WHERE {where};"
        )

    def delete(self, table_name: str, where: str):
        """
        Delete the rows from the table. The where clause is used to filter the
        rows to be deleted.

        Args:
            table_name: The name of the table
            where: The condition to be used in the query
        """
        self.db_cursor.execute(f"DELETE FROM `{table_name}` WHERE {where};")

    def get_table_columns_info(
        self, table_name: str
    ) -> tuple[tuple[Any, ...], ...]:
        """
        Get the columns information from the table

        Args:
            table_name: The name of the table

        Returns:
            The columns information from the table, e.g.
                (name, type, null, key, default, extra)
        """
        self.db_cursor.execute(f"SHOW COLUMNS FROM `{table_name}`;")

        return self.db_cursor.fetchall()

    def get_table_columns(self, table_name: str) -> list[str]:
        """
        Get the columns from the table

        Args:
            table_name: The name of the table

        Returns:
            The columns from the table
        """
        return [
            column[0] for column in self.get_table_columns_info(table_name)
        ]

    def get_table_as_json(self, table_name: str):
        """
        Get the data from the table as a json

        Returns:
            The data from the table as a json
        """
        return [
            dict(zip(self.get_table_columns(table_name), row))
            for row in self.select(table_name)
        ]
