"""
REST API
========

The REST API gateway will be: 127.0.0.1:5000/users/<USER_ID>

1. POST - will accept user_name parameter inside the JSON payload.
A new user will be created in the database with the id passed in the URL and
with user_name passed in the request pay load.
ID has to be unique!

    On success: return JSON: {“status”:“ok”,“user_added”:<USER_NAME>}
                + code: 200

    On error: return JSON: {“status”:“error”,“reason”: ”id already exists”}
              + code: 5002

2. GET - returns the user names to red in the database for a given user id.
Following the example:127.0.0.1:5000/users/1 will return john.

    On success: return JSON: {“status”:“ok”,“user_name”:<USER_NAME>}
                + code: 200

    On error: return JSON: {“status”:“error”,“reason”:”no such id”} + code:500


3. PUT - will modify existing user name (in the database).
Following the above example, when posting the below JSON payload to
127.0.0.1:5000/users/1 george will replace john under the id 1
    {“user_name”:“george”}

    On success:return JSON: {“status”:“ok”,“user_updated”:<USER_NAME>}
    + code: 200

    On error: returnJSON: {“status”:“error”,“reason”:”no such id”}
    + code: 500

4.DELETE - will delete existing user (from database).
Following the above (marked) example, when using delete on
127.0.0.1:5000/users/1. The user under the id 1will be deleted.

    On success:return JSON: {“status”:“ok”,“user_deleted”:<USER_ID>}
    + code: 200

    On error: return JSON:{“status”:“error”,“reason”:”no such id”}
    + code: 500
"""

from flask import Flask, request, jsonify
from flask.wrappers import Response
from pydantic_core import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Any, Literal

from glob_dev_exp_devops_project.exceptions import DBFailureReasonsEnum
from glob_dev_exp_devops_project.db.db_connector import ORM
from glob_dev_exp_devops_project.db.db_utils import (
    HOST,
    PASSWORD,
    PORT,
    SCHEMA_NAME,
    USER_NAME,
    UsersDataModel,
)

# Flask app
app = Flask(__name__)

# Pool of connections for the database
db_engine = create_engine(
    f"mysql+pymysql://{USER_NAME}:{PASSWORD}@{HOST}:{PORT}/{SCHEMA_NAME}",
    pool_recycle=3600,
    pool_reset_on_return=None,
    isolation_level="AUTOCOMMIT",
)
db_session = sessionmaker(bind=db_engine)(expire_on_commit=False)


@app.route("/users/<int:user_id>", methods=["POST"])
def add_user(
    user_id: int,
) -> tuple[Response, Literal[200] | Literal[422] | Literal[500]]:
    """
    Add a new user to the database.

    Args:
        user_id: The user id. It has to be unique.

    Returns:
        Depending on the success or failure of the operation, it will return
        a JSON response with the status and the user added or an error message.
    """
    request_data: dict[str, Any] = request.json  # type: ignore
    # validate the data using pydantic
    try:
        user_data = UsersDataModel.model_validate(request_data)
    except ValidationError as e:
        return jsonify({"status": "error", "reason": str(e)}), 422

    with db_session.connection() as db_conn:
        my_db = ORM(db_cursor=db_conn.connection.cursor(), table_name="users")

        # check if the user_id already exists
        fetched_user_data = my_db.select(
            columns=["user_id"],
            where=f"user_id = {user_id}",
        )
        # if the user_id already exists, return an error
        if fetched_user_data:
            return (
                jsonify(
                    {
                        "status": "error",
                        "reason": DBFailureReasonsEnum.ID_ALREADY_EXISTS,
                    }
                ),
                500,
            )
        # insert the new user
        my_db.insert(
            data=user_data.model_dump(),
        )
    return jsonify({"status": "ok", "user_added": user_data.user_name}), 200


@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(
    user_id: int,
) -> tuple[Response, Literal[500] | Literal[200] | Literal[422]]:
    """
    Get the user name from the database.

    Args:
        user_id: The user id.

    Returns:
        Depending on the success or failure of the operation, it will return
        a JSON response with the status and the user name or an error message.
    """
    with db_session.connection() as db_conn:
        my_db = ORM(db_cursor=db_conn.connection.cursor(), table_name="users")
        fetched_user_data = my_db.select(
            columns=["user_name"], where=f"user_id = {user_id}"
        )
        # if the fetched data is empty, return an error
        if not fetched_user_data:
            return (
                jsonify(
                    {
                        "status": "error",
                        "reason": DBFailureReasonsEnum.NO_SUCH_ID,
                    }
                ),
                500,
            )
        if len(fetched_user_data) > 1:
            # this should never happen
            raise ValueError(f"More than one user with the same id: {user_id}")

        # process the fetched data as json and get the user name
        try:
            processed_data: UsersDataModel = my_db.validate_processed_data(
                validation_model=UsersDataModel, fetched_data=fetched_user_data
            ).pop()
        except ValidationError as e:
            return jsonify({"status": "error", "reason": str(e)}), 422
    return (
        jsonify({"status": "ok", "user_name": processed_data.user_name}),
        200,
    )


@app.route("/users/<int:user_id>", methods=["PUT"])
def update_user(
    user_id: int,
) -> tuple[Response, Literal[200] | Literal[422] | Literal[500]]:
    """
    Update the user name in the database.

    Args:
        user_id: The user id.

    Returns:
        Depending on the success or failure of the operation, it will return
        a JSON response with the status and the user updated or an error message.
    """
    request_data: dict[str, Any] = request.json  # type: ignore
    # validate the request data using pydantic
    try:
        validated_data = UsersDataModel.model_validate(request_data)
    except ValidationError as e:
        return jsonify({"status": "error", "reason": str(e)}), 422

    with db_session.connection() as db_conn:
        my_db = ORM(db_cursor=db_conn.connection.cursor(), table_name="users")
        fetched_user_data = my_db.select(
            columns=["user_name"], where=f"user_id = {user_id}"
        )
        if not fetched_user_data:
            return (
                jsonify(
                    {
                        "status": "error",
                        "reason": DBFailureReasonsEnum.NO_SUCH_ID,
                    }
                ),
                500,
            )
        my_db.update(
            data=validated_data.model_dump(),
            where=f"user_id = {user_id}",
        )

    return (
        jsonify({"status": "ok", "user_updated": validated_data.user_name}),
        200,
    )


@app.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(
    user_id: int,
) -> tuple[Response, Literal[200] | Literal[422] | Literal[500]]:
    """
    Delete the user from the database.

    Args:
        user_id: The user id.

    Returns:
        Depending on the success or failure of the operation, it will return
        a JSON response with the status and the user deleted or an error message.
    """
    with db_session.connection() as db_conn:
        my_db = ORM(db_cursor=db_conn.connection.cursor(), table_name="users")
        fetched_user_data = my_db.select(
            columns=["user_name"], where=f"user_id = {user_id}"
        )
        if not fetched_user_data:
            return (
                jsonify(
                    {
                        "status": "error",
                        "reason": DBFailureReasonsEnum.NO_SUCH_ID,
                    }
                ),
                500,
            )
        my_db.delete(where=f"user_id = {user_id}")

    return jsonify({"status": "ok", "user_deleted": user_id}), 200
