"""Environment variable loader for PDF Manipulator."""
import os
from pathlib import Path
from typing import Dict, Optional

# Import the configured logger to ensure consistent logging
try:
    from .logging_config import get_logger
    logger = get_logger('env_loader')
except ImportError:
    # Fallback to standard logging if logging_config is not available
    import logging
    logger = logging.getLogger(__name__)

def load_dotenv(env_path: Optional[str] = None) -> Dict[str, str]:
    """Load environment variables from .env file.
    
    Args:
        env_path: Path to .env file. If None, will search in project root and parent directories.
        
    Returns:
        Dictionary with loaded environment variables.
    """
    # Find .env file if not specified
    if env_path is None:
        # Start from current working directory
        search_path = Path.cwd()
        # Also check project root if we're in a subdirectory
        potential_paths = [
            search_path / '.env',
            search_path.parent / '.env',
            search_path.parent.parent / '.env',
            Path(__file__).parent.parent.parent / '.env'  # Project root
        ]
        
        for path in potential_paths:
            if path.exists():
                env_path = str(path)
                logger.debug(f"Found .env file at: {env_path}")
                break
    
    if env_path is None or not Path(env_path).exists():
        logger.debug("No .env file found")
        return {}
    
    # Load variables from .env file
    env_vars = {}
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Parse key=value format
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Remove quotes if present
                if (value.startswith('"') and value.endswith('"')) or \
                   (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]
                
                # Only set if not already in environment
                if key and key not in os.environ:
                    os.environ[key] = value
                    env_vars[key] = value
                    logger.debug(f"Loaded environment variable: {key}")
    
    # Check for important API keys
    important_keys = [
        'OPENAI_API_KEY', 
        'OLLAMA_BASE_URL',
        'LLM_ENDPOINT_URL',
        'LLM_API_TOKEN'
    ]
    
    for key in important_keys:
        if key in os.environ:
            # Mask API keys in logs for security
            if 'KEY' in key or 'TOKEN' in key:
                logger.info(f"Found {key} in environment")
            else:
                logger.info(f"Found {key} in environment: {os.environ[key]}")
    
    return env_vars