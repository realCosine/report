import os
import json

def load_config():
    config = {}

    global_config_path = os.path.join(os.path.dirname(__file__), "..", "global.config")
    module_config_path = os.path.join(os.path.dirname(__file__), ".config")

    assert os.path.exists(global_config_path), f"Global config file not found: {global_config_path}"
    with open(global_config_path, "r") as global_config_file:
        config.update(json.load(global_config_file))

    assert os.path.exists(module_config_path), f"Module config file not found: {module_config_path}"
    with open(module_config_path, "r") as module_config_file:
        config.update(json.load(module_config_file))

    return config
