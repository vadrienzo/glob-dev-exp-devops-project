"""
1. The web interface will return the user name of a given user id stored inside
users table (please refer to Database section).

2. The user name of the user will be returned in an HTML format with a locator
to simplify testing.

3. In case the ID doesn't exist return an error (in HTML format)
"""

import os
from pathlib import Path
import requests

from flask import Flask, render_template

from glob_dev_exp_devops_project.server.rest_app import (
    SERVER_RUN_HOST,
    SERVER_RUN_PORT,
)

# Flask connection details
CLIENT_RUN_HOST = os.environ.get("CLIENT_RUN_HOST", "127.0.0.1")
CLIENT_RUN_PORT = int(os.environ.get("CLIENT_RUN_PORT", 8001))
CLIENT_TEMPLATE_FOLDER = (
    Path(__file__).parent / ".." / ".." / "templates" / "client"
)


# Flask app
def create_flask_app(
    template_folder: Path = Path(__file__).parent / "templates",
):
    return Flask(__name__, template_folder=template_folder)


web_app = create_flask_app(template_folder=CLIENT_TEMPLATE_FOLDER)

# How is the interaction between the frontend and the backend?
# The frontend will send a GET request to the backend with the user ID
# The backend will query the database and return the user name


@web_app.route("/get_user_data")
@web_app.route("/get_user_data/<int:user_id>", methods=["GET"])
def get_user_name(user_id: int):
    # Get the user name from the backend
    response = requests.get(
        f"http://{SERVER_RUN_HOST}:{SERVER_RUN_PORT}/users/{user_id}"
    )
    user_name = response.json().get("user_name")
    return f"User name: {user_name}"


@web_app.route("/index")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    web_app.run(host=CLIENT_RUN_HOST, port=CLIENT_RUN_PORT, debug=True)
