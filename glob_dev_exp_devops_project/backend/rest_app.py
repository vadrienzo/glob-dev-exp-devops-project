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

from enum import Enum
from typing import Any, Literal
from flask import Flask, request, jsonify
from flask.wrappers import Response

app = Flask(__name__)

# Database
users = {}


class ReasonsEnum(str, Enum):
    ID_ALREADY_EXISTS = "id already exists"
    NO_SUCH_ID = "no such id"


@app.route("/users/<int:user_id>", methods=["POST"])
def add_user(
    user_id: int,
) -> tuple[Response, Literal[5002]] | tuple[Response, Literal[200]]:
    """
    Add a new user to the database.

    Args:
        user_id: The user id. It has to be unique.

    Returns:
        Depending on the success or failure of the operation, it will return
        a JSON response with the status and the user added or an error message.
    """
    request_data: dict[str, Any] = request.json  # type: ignore
    user_name: str = request_data.get("user_name")  # type: ignore
    if user_id in users:
        return (
            jsonify(
                {"status": "error", "reason": ReasonsEnum.ID_ALREADY_EXISTS}
            ),
            5002,
        )
    users[user_id] = user_name
    return jsonify({"status": "ok", "user_added": user_name}), 200


@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(
    user_id: int,
) -> tuple[Response, Literal[500]] | tuple[Response, Literal[200]]:
    """
    Get the user name from the database.

    Args:
        user_id: The user id.

    Returns:
        Depending on the success or failure of the operation, it will return
        a JSON response with the status and the user name or an error message.
    """
    if user_id not in users:
        return (
            jsonify({"status": "error", "reason": ReasonsEnum.NO_SUCH_ID}),
            500,
        )
    return jsonify({"status": "ok", "user_name": users[user_id]}), 200


@app.route("/users/<int:user_id>", methods=["PUT"])
def update_user(
    user_id: int,
) -> tuple[Response, Literal[500]] | tuple[Response, Literal[200]]:
    """
    Update the user name in the database.

    Args:
        user_id: The user id.

    Returns:
        Depending on the success or failure of the operation, it will return
        a JSON response with the status and the user updated or an error message.
    """
    request_data: dict[str, Any] = request.json  # type: ignore
    user_name: str = request_data.get("user_name")  # type: ignore
    if user_id not in users:
        return (
            jsonify({"status": "error", "reason": ReasonsEnum.NO_SUCH_ID}),
            500,
        )
    users[user_id] = user_name
    return jsonify({"status": "ok", "user_updated": user_name}), 200


@app.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(
    user_id: int,
) -> tuple[Response, Literal[500]] | tuple[Response, Literal[200]]:
    """
    Delete the user from the database.

    Args:
        user_id: The user id.

    Returns:
        Depending on the success or failure of the operation, it will return
        a JSON response with the status and the user deleted or an error message.
    """
    if user_id not in users:
        return (
            jsonify({"status": "error", "reason": ReasonsEnum.NO_SUCH_ID}),
            500,
        )
    del users[user_id]
    return jsonify({"status": "ok", "user_deleted": user_id}), 200
