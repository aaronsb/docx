"""Configuration system for the PDF manipulator toolkit.

This module provides functionality to load, validate, and manage configuration
settings from YAML files with helpful comments.
"""
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
import yaml
from dataclasses import dataclass

from pdf_manipulator.core.exceptions import PDFManipulatorError

# Define paths for configuration
DEFAULT_CONFIG_NAME = "config.yaml"
USER_CONFIG_DIR = os.path.expanduser("~/.config/pdf_manipulator")
PROJECT_CONFIG_DIR = os.path.join(os.getcwd(), ".pdf_manipulator")


@dataclass
class ConfigPaths:
    """Paths for configuration files."""
    
    system_config: Path  # Built-in default config
    user_config: Path    # User-specific config at ~/.config/pdf_manipulator
    project_config: Path  # Project-specific config at ./.pdf_manipulator
    custom_config: Optional[Path] = None  # Explicitly provided config path


class ConfigurationError(PDFManipulatorError):
    """Error in configuration loading or validation."""
    pass


def ensure_dir(dir_path: Union[str, Path]) -> None:
    """Ensure a directory exists."""
    Path(dir_path).mkdir(parents=True, exist_ok=True)


def find_config_file(custom_path: Optional[str] = None) -> Path:
    """Find the most appropriate configuration file.
    
    Priority order:
    1. Custom path provided explicitly
    2. Project-specific config: ./.pdf_manipulator/config.yaml
    3. User-specific config: ~/.config/pdf_manipulator/config.yaml
    4. System default config (package built-in)
    
    Args:
        custom_path: Optional custom path to configuration file
        
    Returns:
        Path to the configuration file to use
        
    Raises:
        ConfigurationError: If the custom path is provided but doesn't exist
    """
    # Get the system default config path from the package
    package_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    system_config = os.path.join(package_dir, "config", DEFAULT_CONFIG_NAME)
    
    # Check for custom path
    if custom_path:
        custom_path = os.path.expanduser(custom_path)
        if os.path.exists(custom_path):
            return Path(custom_path)
        else:
            raise ConfigurationError(f"Custom config file not found: {custom_path}")
    
    # Check for project config
    project_config = os.path.join(PROJECT_CONFIG_DIR, DEFAULT_CONFIG_NAME)
    if os.path.exists(project_config):
        return Path(project_config)
    
    # Check for user config
    user_config = os.path.join(USER_CONFIG_DIR, DEFAULT_CONFIG_NAME)
    if os.path.exists(user_config):
        return Path(user_config)
    
    # Fall back to system default
    if os.path.exists(system_config):
        return Path(system_config)
    
    # If we get here, no config file was found
    raise ConfigurationError(
        f"No configuration file found. Please create a config file at {user_config}"
    )


def get_all_config_paths() -> ConfigPaths:
    """Get paths to all possible configuration files.
    
    Returns:
        ConfigPaths object with all potential configuration paths
    """
    package_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    system_config = Path(os.path.join(package_dir, "config", DEFAULT_CONFIG_NAME))
    user_config = Path(os.path.join(USER_CONFIG_DIR, DEFAULT_CONFIG_NAME))
    project_config = Path(os.path.join(PROJECT_CONFIG_DIR, DEFAULT_CONFIG_NAME))
    
    return ConfigPaths(
        system_config=system_config,
        user_config=user_config,
        project_config=project_config
    )


def _substitute_env_vars(config: Dict[str, Any]) -> None:
    """Recursively substitute environment variables in config.
    
    Args:
        config: Configuration dictionary to modify in place
    """
    for key, value in list(config.items()):
        if isinstance(value, dict):
            _substitute_env_vars(value)
        elif isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            env_var = value[2:-1]
            env_value = os.getenv(env_var)
            if env_value:
                config[key] = env_value


def load_config(path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """Load configuration from a YAML file.
    
    Args:
        path: Optional path to configuration file.
            If not provided, uses the default search path.
            
    Returns:
        Configuration dictionary with environment variables substituted
        
    Raises:
        ConfigurationError: If configuration cannot be loaded
    """
    try:
        # Find the config file to use
        if path:
            config_path = Path(path)
        else:
            config_path = find_config_file()
        
        # Load the configuration
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        if config is None:
            config = {}  # Handle empty config file
        
        # Substitute environment variables
        _substitute_env_vars(config)
        
        return config
    
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Invalid YAML in configuration file: {e}")
    
    except Exception as e:
        raise ConfigurationError(f"Failed to load configuration: {e}")


def save_config(config: Dict[str, Any], path: Union[str, Path]) -> None:
    """Save configuration to a YAML file with comments preserved.
    
    Args:
        config: Configuration dictionary
        path: Path to save the configuration file
        
    Raises:
        ConfigurationError: If configuration cannot be saved
    """
    try:
        # Ensure the directory exists
        ensure_dir(os.path.dirname(path))
        
        # Save the configuration
        with open(path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    except Exception as e:
        raise ConfigurationError(f"Failed to save configuration: {e}")


def create_default_config(path: Union[str, Path]) -> None:
    """Create a default configuration file with helpful comments.
    
    Args:
        path: Path to save the default configuration
        
    Raises:
        ConfigurationError: If default configuration cannot be created
    """
    # Load the default configuration template from the package
    package_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_path = os.path.join(package_dir, "config", "default_config.yaml")
    
    try:
        # Ensure the directory exists
        ensure_dir(os.path.dirname(path))
        
        # Copy the template to the destination
        if os.path.exists(template_path):
            with open(template_path, 'r') as src, open(path, 'w') as dst:
                dst.write(src.read())
        else:
            # Create a minimal default configuration
            default_config = {
                "general": {
                    "output_dir": "output",
                    "logging": {
                        "level": "INFO",
                        "file": None,
                    }
                },
                "rendering": {
                    "dpi": 300,
                    "alpha": False,
                    "zoom": 1.0,
                },
                "ocr": {
                    "language": "eng",
                    "tessdata_dir": None,
                    "tesseract_cmd": None,
                },
                "intelligence": {
                    "default_backend": "ollama",
                    "backends": {
                        "ollama": {
                            "model": "llava:latest",
                            "base_url": "http://localhost:11434",
                            "timeout": 120,
                        },
                        "llama_cpp": {
                            "model_path": None,
                            "n_ctx": 2048,
                            "n_gpu_layers": -1,
                        },
                        "llama_cpp_http": {
                            "base_url": "http://localhost:8080",
                            "model": None,
                            "timeout": 120,
                            "n_predict": 2048,
                            "temperature": 0.1,
                        }
                    }
                }
            }
            
            # Add comments to the configuration
            comments = [
                "# PDF Manipulator Configuration",
                "#",
                "# This file defines settings for the PDF Manipulator toolkit",
                "# Uncomment and modify settings as needed",
                "#",
                "# For more details, see the documentation:",
                "# https://github.com/yourusername/pdf_manipulator/blob/main/docs/configuration.md",
            ]
            
            with open(path, 'w') as f:
                f.write("\n".join(comments) + "\n\n")
                yaml.dump(default_config, f, default_flow_style=False, sort_keys=False)
    
    except Exception as e:
        raise ConfigurationError(f"Failed to create default configuration: {e}")


def validate_config(config: Dict[str, Any]) -> List[str]:
    """Validate the configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        List of validation warnings
    """
    warnings = []
    
    # Check for required sections
    required_sections = ["general", "rendering", "ocr", "intelligence"]
    for section in required_sections:
        if section not in config:
            warnings.append(f"Missing required section: {section}")
    
    # Check intelligence section
    if "intelligence" in config:
        intelligence = config["intelligence"]
        
        # Check default backend
        if "default_backend" not in intelligence:
            warnings.append("No default intelligence backend specified")
        elif intelligence["default_backend"] not in ["ollama", "llama_cpp", "llama_cpp_http"]:
            warnings.append(f"Invalid default intelligence backend: {intelligence['default_backend']}")
        
        # Check backends
        if "backends" not in intelligence:
            warnings.append("No intelligence backends defined")
        else:
            backends = intelligence["backends"]
            
            # Check Ollama backend
            if "ollama" in backends:
                ollama = backends["ollama"]
                if "model" not in ollama:
                    warnings.append("No model specified for Ollama backend")
                if "base_url" not in ollama:
                    warnings.append("No base URL specified for Ollama backend")
            
            # Check llama.cpp backend
            if "llama_cpp" in backends:
                llama_cpp = backends["llama_cpp"]
                if "model_path" not in llama_cpp or not llama_cpp["model_path"]:
                    warnings.append("No model path specified for llama.cpp backend")
            
            # Check llama.cpp HTTP backend
            if "llama_cpp_http" in backends:
                llama_cpp_http = backends["llama_cpp_http"]
                if "base_url" not in llama_cpp_http:
                    warnings.append("No base URL specified for llama.cpp HTTP backend")
    
    return warnings


def get_nested_value(config: Dict[str, Any], keys: List[str], default: Any = None) -> Any:
    """Get a value from nested dictionaries with a fallback to default.
    
    Args:
        config: Configuration dictionary
        keys: List of keys to traverse
        default: Default value if key not found
        
    Returns:
        Value from config or default
    """
    current = config
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current


def setup_user_config() -> None:
    """Set up user configuration if it doesn't exist."""
    config_dir = Path(USER_CONFIG_DIR)
    config_file = config_dir / DEFAULT_CONFIG_NAME
    
    if not config_file.exists():
        create_default_config(config_file)
        print(f"Created default configuration at {config_file}")


def init_project_config() -> None:
    """Initialize project-specific configuration."""
    config_dir = Path(PROJECT_CONFIG_DIR)
    config_file = config_dir / DEFAULT_CONFIG_NAME
    
    if not config_file.exists():
        create_default_config(config_file)
        print(f"Initialized project configuration at {config_file}")