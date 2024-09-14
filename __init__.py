import os
import json

workspace_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
config_path = os.path.join(workspace_dir, ".config")


def load_config():
    with open(config_path, "r") as config_file:
        return json.load(config_file)
