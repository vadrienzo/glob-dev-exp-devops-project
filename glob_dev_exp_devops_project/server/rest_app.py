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

import os
from pathlib import Path
from typing import Any, Literal

from flask import Flask, abort, jsonify, request
from flask.wrappers import Response
from pydantic_core import ValidationError

from glob_dev_exp_devops_project.db.db_connector import (
    add_user_data,
    create_table,
    delete_user_data,
    get_connection,
    get_user_from_database,
    update_user_data,
)
from glob_dev_exp_devops_project.db.db_utils import UsersDataModel
from glob_dev_exp_devops_project.exceptions import (
    DBFailureReasonsEnum,
    ServerFailureReasonsEnum,
)

# Flask connection details
SERVER_RUN_HOST = os.environ.get("SERVER_RUN_HOST", "127.0.0.1")
SERVER_RUN_PORT = int(os.environ.get("SERVER_RUN_PORT", 5000))
SERVER_HTML_TEMPLATE_FOLDER = (
    Path(__file__).parent / ".." / ".." / "templates" / "server"
)
SERVER_CSS_STATIC_FOLDER = Path(__file__).parent / ".." / ".." / "static"


# Flask app
def create_flask_app(
    template_folder: Path = Path(__file__).parent / "templates",
    static_folder: Path = Path(__file__).parent / "static",
):
    app = Flask(
        __name__, template_folder=template_folder, static_folder=static_folder
    )
    # app.register_error_handler(404, page_not_found)
    # app.register_error_handler(500, internal_server_error)
    # app.register_error_handler(422, invalid_request)
    return app


rest_app = create_flask_app(
    template_folder=SERVER_HTML_TEMPLATE_FOLDER,
    static_folder=SERVER_CSS_STATIC_FOLDER,
)


@rest_app.route("/users")
@rest_app.route("/users/<int:user_id>", methods=["POST"])
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
    request_data: dict[str, Any] = jsonify(request.form).json  # type: ignore
    # validate the data using pydantic
    try:
        new_user_data = UsersDataModel.model_validate(request_data)
    except ValidationError as e:
        return abort(422, str(e))

    return add_user_data(
        db_connection=get_connection(),
        user_id=user_id,
        new_user_data=new_user_data,
    )


@rest_app.route("/users")
@rest_app.route("/users/<int:user_id>", methods=["GET"])
def get_user(
    user_id: int,
) -> tuple[Response, Literal[500] | Literal[200] | Literal[422]]:
    # ) -> tuple[dict[str, Any], Literal[200]]:
    """
    Get the user name from the database.

    Args:
        user_id: The user id.

    Returns:
        Depending on the success or failure of the operation, it will return
        a JSON response with the status and the user name or an error message.
    """
    return get_user_from_database(
        db_connection=get_connection(), user_id=user_id
    )


@rest_app.route("/users")
@rest_app.route("/users/<int:user_id>", methods=["PUT"])
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
        return abort(422, str(e))

    return update_user_data(
        db_connection=get_connection(),
        user_id=user_id,
        validated_data=validated_data,
    )


@rest_app.route("/users")
@rest_app.route("/users/<int:user_id>", methods=["DELETE"])
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
    return delete_user_data(db_connection=get_connection(), user_id=user_id)


@rest_app.errorhandler(code_or_exception=404)
def page_not_found(e) -> tuple[Response, Literal[500]]:
    return (
        jsonify(
            {"status": "error", "reason": DBFailureReasonsEnum.NO_SUCH_ID}
        ),
        500,
    )


@rest_app.errorhandler(code_or_exception=500)
def internal_server_error(e) -> tuple[Response, Literal[500]]:
    return (
        jsonify(
            {
                "status": "error",
                "reason": ServerFailureReasonsEnum.INTERNAL_SERVER_ERROR,
            }
        ),
        500,
    )


@rest_app.errorhandler(code_or_exception=422)
def invalid_request(e) -> tuple[Response, Literal[422]]:
    return (
        jsonify(
            {
                "status": "error",
                "reason": ServerFailureReasonsEnum.INVALID_REQUEST,
            }
        ),
        422,
    )


if __name__ == "__main__":
    # create tables in the database
    create_table(db_connection=get_connection(), table_name="users")
    rest_app.run(host=SERVER_RUN_HOST, port=SERVER_RUN_PORT, debug=True)
