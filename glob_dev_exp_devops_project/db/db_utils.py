"""
Utils to interact with the database
===================================
"""

SCHEMA_NAME = "mydb"
USER_NAME = "project_user "
PASSWORD = "password"
PORT = 3306
HOST = "127.0.0.1"

# Table schema
TABLES_AND_TABLE_SCHEMAS = {
    "users": {
        "user_id": "INT NOT NULL ",
        "user_ame": "VARCHAR(50) NOT NULL",
        "creation_date": "VARCHAR(50) NOT NULL",
        "primary_key": "user_id",
    }
}
