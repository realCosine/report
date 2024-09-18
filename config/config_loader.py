import os
from typing import Any
import logging
import yaml
from pydantic import ValidationError

from .report_config import Config, ReportConfig
from ...core_config import CoreConfig 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_config() -> Config:
    """
    Loads and validates configuration from core_config.yaml and report_config.yaml files.
    
    Returns:
        Config: The combined configuration object.
    
    Raises:
        FileNotFoundError: If any configuration file is missing.
        yaml.YAMLError: If any configuration file contains invalid YAML.
        pydantic.ValidationError: If the configuration does not conform to the Pydantic models.
    """
    current_dir = os.path.dirname(__file__)
    core_path = os.path.abspath(
        os.path.join(current_dir, "..", "..", "core_config.yaml")
    )
    report_path = os.path.join(current_dir, "report_config.yaml")

    if not os.path.exists(core_path):
        logger.error(f"Global config file not found: {core_path}")
        raise FileNotFoundError(f"Global config file not found: {core_path}")
    if not os.path.exists(report_path):
        logger.error(f"Module config file not found: {report_path}")
        raise FileNotFoundError(f"Module config file not found: {report_path}")

    logger.info(f"Loading global configuration from {core_path}")
    try:
        with open(core_path, "r") as core_file:
            core_data = yaml.safe_load(core_file)
    except yaml.YAMLError as e:
        logger.error(f"Error parsing core_config.yaml: {e}")
        raise

    try:
        core = CoreConfig(**core_data)
    except ValidationError as e:
        logger.error(f"Validation error in core_config.yaml: {e}")
        raise

    logger.info(f"Loading module-specific configuration from {report_path}")
    try:
        with open(report_path, "r") as report_file:
            report_data = yaml.safe_load(report_file)
    except yaml.YAMLError as e:
        logger.error(f"Error parsing report_config.yaml: {e}")
        raise

    try:
        report = ReportConfig(**report_data)
    except ValidationError as e:
        logger.error(f"Validation error in report_config.yaml: {e}")
        raise

    try:
        config = Config(core=core, report=report)
    except ValidationError as e:
        logger.error(f"Error combining configurations into Config: {e}")
        raise

    logger.info("Configuration loaded and validated successfully.")

    config.prepare_dirs()
    
    return config