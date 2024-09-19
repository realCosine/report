import os
from typing import Any
import logging
import yaml
from pydantic import ValidationError

from core_config.core_config_loader import load_core_config
from report.config import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_report_config_path():
    """
    Returns the absolute path to the report_config.yaml file.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, "report_config.yaml")


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
    core_config = load_core_config()

    current_dir = os.path.dirname(__file__)
    report_config_path = get_report_config_path()
    try:
        with open(report_config_path, 'r') as file:
            report_config = yaml.safe_load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"Config file not found at: {report_config_path}")
    except yaml.YAMLError as e:
        raise RuntimeError(f"Error parsing YAML file at: {report_config_path}, Error: {e}")

    try:
        report = ReportConfig(**report_config)
    except ValidationError as e:
        logger.error(f"Validation error in report_config.yaml: {e}")
        raise

    try:
        config = Config(core=core_config, report=report)
    except ValidationError as e:
        logger.error(f"Error combining configurations into Config: {e}")
        raise

    logger.info("Configuration loaded and validated successfully.")

    config.prepare_dirs()
    
    return config