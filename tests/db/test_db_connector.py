from glob_dev_exp_devops_project.db.db_connector import ORM

from unittest import mock


class TestORM:
    def test_create_table(self):
        mock_cursor = mock.MagicMock()
        mock_cursor.connection.autocommit = mock.MagicMock(return_value=False)

        orm = ORM(db_cursor=mock_cursor, auto_commit=True)
        orm.create_table(
            schema_name="mydb",
            table_name="users",
            table_schema={
                "user_id": "INT NOT NULL ",
                "user_ame": "VARCHAR(50) NOT NULL",
                "creation_date": "VARCHAR(50) NOT NULL",
                "primary_key": "user_id",
            },
        )
        query = "CREATE TABLE `mydb`.`users`(`user_id` INT NOT NULL , `user_ame` VARCHAR(50) NOT NULL, `creation_date` VARCHAR(50) NOT NULL, PRIMARY KEY (`user_id`));"
        orm.db_cursor.execute.assert_called_once_with(query)

    def test_query_table(self):
        mock_cursor = mock.MagicMock()
        mock_cursor.connection.autocommit = mock.MagicMock(return_value=False)

        orm = ORM(db_cursor=mock_cursor, auto_commit=True)
        orm.query(
            query="SELECT * FROM users WHERE user_id = 1",
        )
        orm.db_cursor.execute.assert_called_once_with(
            "SELECT * FROM users WHERE user_id = 1"
        )

    def test_insert_into_table(self):
        mock_cursor = mock.MagicMock()
        mock_cursor.connection.autocommit = mock.MagicMock(return_value=False)

        orm = ORM(db_cursor=mock_cursor, auto_commit=True)
        orm.insert(
            table_name="users",
            data={
                "user_id": 1,
                "user_name": "user1",
                "creation_date": "2021-01-01 00:00:00",
            },
        )
        orm.db_cursor.execute.assert_called_once_with(
            "INSERT INTO `users` (`data`) VALUES ('{'user_id': 1, 'user_name': 'user1', 'creation_date': '2021-01-01 00:00:00'}');"
        )

    def test_update_table(self):
        mock_cursor = mock.MagicMock()
        mock_cursor.connection.autocommit = mock.MagicMock(return_value=False)

        orm = ORM(db_cursor=mock_cursor, auto_commit=True)
        orm.update(
            table_name="users",
            data={"user_name": "user2"},
            where="user_id = 1",
        )
        orm.db_cursor.execute.assert_called_once_with(
            "UPDATE `users` SET `data` = '{'user_name': 'user2'}' WHERE user_id = 1;"
        )

    def test_delete_from_table(self):
        mock_cursor = mock.MagicMock()
        mock_cursor.connection.autocommit = mock.MagicMock(return_value=False)

        orm = ORM(db_cursor=mock_cursor, auto_commit=True)
        orm.delete(
            table_name="users",
            where="user_id = 1",
        )
        orm.db_cursor.execute.assert_called_once_with(
            "DELETE FROM `users` WHERE user_id = 1;"
        )

    def test_select_from_table(self):
        mock_cursor = mock.MagicMock()
        mock_cursor.connection.autocommit = mock.MagicMock(return_value=False)

        orm = ORM(db_cursor=mock_cursor, auto_commit=True)
        orm.select(
            table_name="users",
            columns=["user_id", "user_name"],
            where="user_id = 1",
        )
        orm.db_cursor.execute.assert_called_once_with(
            "SELECT `user_id`, `user_name` FROM `users` WHERE user_id = 1"
        )

    def test_get_table_columns_info(self):
        mock_cursor = mock.MagicMock()
        mock_cursor.connection.autocommit = mock.MagicMock(return_value=False)

        orm = ORM(db_cursor=mock_cursor, auto_commit=True)
        orm.get_table_columns_info(
            table_name="users",
        )
        orm.db_cursor.execute.assert_called_once_with(
            "SHOW COLUMNS FROM `users`;"
        )

    def test_get_table_columns(self):
        mock_cursor = mock.MagicMock()
        mock_cursor.connection.autocommit = mock.MagicMock(return_value=False)

        orm = ORM(db_cursor=mock_cursor, auto_commit=True)
        orm.get_table_columns(
            table_name="users",
        )
        # The method get_table_columns_info is called inside get_table_columns
        orm.db_cursor.execute.assert_called_once_with(
            "SHOW COLUMNS FROM `users`;"
        )
