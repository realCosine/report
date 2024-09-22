from pathlib import Path
from typing import Any
import logging
import yaml
from pydantic import ValidationError

from report.config import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_report_config_path():
    """
    Returns the absolute path to the report_config.yaml file.
    """
    return Path(__file__).resolve().parent / "report_config.yaml"


def load_report_config() -> Config:
    """
    Loads and validates configuration from core_config.yaml and report_config.yaml files.

    Returns:
        Config: The combined configuration object.

    Raises:
        FileNotFoundError: If any configuration file is missing.
        yaml.YAMLError: If any configuration file contains invalid YAML.
        pydantic.ValidationError: If the configuration does not conform to the Pydantic models.
    """
    from core_config import load_core_config
    from utils import load_yaml_config

    core_config = load_core_config()

    report_config_path = get_report_config_path()
    report_config_data = load_yaml_config(report_config_path)

    report_config = ReportConfig(**report_config_data)

    try:
        config = Config(core=core_config, report=report_config)
    except ValidationError as e:
        logger.error(f"Error combining configurations into Config: {e}")
        raise

    logger.info("Configuration loaded and validated successfully.")

    config.prepare_dirs()

    return config
