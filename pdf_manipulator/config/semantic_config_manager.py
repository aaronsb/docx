"""Configuration manager for semantic pipeline."""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union
import logging
from dataclasses import dataclass, field
from copy import deepcopy


@dataclass
class SemanticPipelineConfig:
    """Configuration for semantic pipeline processing."""
    # LLM Backend
    llm_backend_type: str = "ollama"
    llm_backend_config: Dict[str, Any] = field(default_factory=dict)
    
    # Pipeline settings
    enable_llm: bool = True
    max_pages: Optional[int] = None
    parallel_pages: int = 4
    context_window: int = 4096
    confidence_threshold: float = 0.7
    enable_ocr_fallback: bool = True
    save_intermediate: bool = False
    output_format: str = "json"
    
    # Structure discovery
    prefer_native_toc: bool = True
    fallback_to_markitdown: bool = True
    heading_confidence: float = 0.6
    
    # Content analysis
    use_word_stems: bool = True
    bayesian_threshold: float = 0.3
    min_term_frequency: int = 2
    enable_relationships: bool = True
    
    # Semantic enhancement
    max_context_tokens: int = 4096
    context_summaries: int = 3
    
    # Graph construction
    edge_decay_rate: float = 0.1
    semantic_multiplier: float = 1.5
    
    # Performance
    cache_enabled: bool = True
    cache_ttl: int = 3600
    max_graph_nodes: int = 10000
    max_graph_edges: int = 50000
    
    # Output
    json_pretty_print: bool = True
    sqlite_domain_name: str = "documents"
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'SemanticPipelineConfig':
        """Create config from dictionary."""
        config = cls()
        
        # LLM Backend
        llm_config = config_dict.get("llm_backend", {})
        config.llm_backend_type = llm_config.get("type", "ollama")
        config.llm_backend_config = llm_config.get("backends", {}).get(config.llm_backend_type, {})
        
        # Pipeline
        pipeline = config_dict.get("pipeline", {})
        config.enable_llm = pipeline.get("enable_llm", True)
        config.max_pages = pipeline.get("max_pages")
        config.parallel_pages = pipeline.get("parallel_pages", 4)
        config.context_window = pipeline.get("context_window", 4096)
        config.confidence_threshold = pipeline.get("confidence_threshold", 0.7)
        config.enable_ocr_fallback = pipeline.get("enable_ocr_fallback", True)
        config.save_intermediate = pipeline.get("save_intermediate", False)
        config.output_format = pipeline.get("output_format", "json")
        
        # Structure discovery
        structure = config_dict.get("structure_discovery", {})
        config.prefer_native_toc = structure.get("prefer_native_toc", True)
        config.fallback_to_markitdown = structure.get("fallback_to_markitdown", True)
        config.heading_confidence = structure.get("heading_confidence", 0.6)
        
        # Content analysis
        content = config_dict.get("content_analysis", {})
        config.use_word_stems = content.get("use_word_stems", True)
        config.bayesian_threshold = content.get("bayesian_threshold", 0.3)
        config.min_term_frequency = content.get("min_term_frequency", 2)
        config.enable_relationships = content.get("relationship_detection", {}).get("enabled", True)
        
        # Semantic enhancement
        semantic = config_dict.get("semantic_enhancement", {})
        config.max_context_tokens = semantic.get("max_context_tokens", 4096)
        config.context_summaries = semantic.get("context_summaries", 3)
        
        # Graph construction
        graph = config_dict.get("graph_construction", {})
        edge_scoring = graph.get("edge_scoring", {})
        config.edge_decay_rate = edge_scoring.get("decay_rate", 0.1)
        config.semantic_multiplier = edge_scoring.get("semantic_multiplier", 1.5)
        
        # Performance
        performance = config_dict.get("performance", {})
        cache = performance.get("cache", {})
        config.cache_enabled = cache.get("enabled", True)
        config.cache_ttl = cache.get("ttl", 3600)
        memory = performance.get("memory", {})
        config.max_graph_nodes = memory.get("max_graph_nodes", 10000)
        config.max_graph_edges = memory.get("max_graph_edges", 50000)
        
        # Output
        output = config_dict.get("output", {})
        json_config = output.get("json", {})
        config.json_pretty_print = json_config.get("pretty_print", True)
        sqlite_config = output.get("sqlite", {})
        domain = sqlite_config.get("domain", {})
        config.sqlite_domain_name = domain.get("name", "documents")
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "llm_backend": {
                "type": self.llm_backend_type,
                "config": self.llm_backend_config
            },
            "pipeline": {
                "enable_llm": self.enable_llm,
                "max_pages": self.max_pages,
                "parallel_pages": self.parallel_pages,
                "context_window": self.context_window,
                "confidence_threshold": self.confidence_threshold,
                "enable_ocr_fallback": self.enable_ocr_fallback,
                "save_intermediate": self.save_intermediate,
                "output_format": self.output_format
            },
            # ... other sections
        }


class SemanticConfigManager:
    """Manages configuration for the semantic pipeline."""
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None,
                 logger: Optional[logging.Logger] = None):
        """Initialize configuration manager.
        
        Args:
            config_path: Path to configuration file
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.config_path = Path(config_path) if config_path else None
        self.config_dict: Dict[str, Any] = {}
        self.config: SemanticPipelineConfig = SemanticPipelineConfig()
        
        # Load configuration
        if self.config_path:
            self.load_config(self.config_path)
        else:
            self.load_default_config()
    
    def load_config(self, config_path: Union[str, Path]):
        """Load configuration from file."""
        config_path = Path(config_path)
        
        if not config_path.exists():
            self.logger.warning(f"Config file not found: {config_path}")
            self.load_default_config()
            return
        
        try:
            with open(config_path, 'r') as f:
                self.config_dict = yaml.safe_load(f)
            
            # Substitute environment variables
            self._substitute_env_vars(self.config_dict)
            
            # Create config object
            self.config = SemanticPipelineConfig.from_dict(self.config_dict)
            
            self.logger.info(f"Loaded configuration from {config_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            self.load_default_config()
    
    def load_default_config(self):
        """Load default configuration."""
        default_config_path = Path(__file__).parent / "semantic_pipeline_config.yaml"
        
        if default_config_path.exists():
            self.load_config(default_config_path)
        else:
            self.logger.warning("Using hardcoded default configuration")
            self.config = SemanticPipelineConfig()
    
    def save_config(self, config_path: Optional[Union[str, Path]] = None):
        """Save configuration to file."""
        save_path = Path(config_path) if config_path else self.config_path
        
        if not save_path:
            raise ValueError("No config path specified")
        
        # Ensure directory exists
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert config to dict
        config_dict = self.config.to_dict()
        
        try:
            with open(save_path, 'w') as f:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            
            self.logger.info(f"Saved configuration to {save_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")
            raise
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot notation key."""
        keys = key.split('.')
        value = self.config_dict
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """Set configuration value by dot notation key."""
        keys = key.split('.')
        config = self.config_dict
        
        # Navigate to the parent
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
        
        # Update config object
        self.config = SemanticPipelineConfig.from_dict(self.config_dict)
    
    def get_llm_backend_config(self) -> Dict[str, Any]:
        """Get LLM backend configuration."""
        backend_type = self.config.llm_backend_type
        backends = self.config_dict.get("llm_backend", {}).get("backends", {})
        return backends.get(backend_type, {})
    
    def get_pipeline_config(self) -> SemanticPipelineConfig:
        """Get pipeline configuration object."""
        return self.config
    
    def _substitute_env_vars(self, config: Dict[str, Any]):
        """Recursively substitute environment variables in config."""
        for key, value in config.items():
            if isinstance(value, dict):
                self._substitute_env_vars(value)
            elif isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                env_var = value[2:-1]
                env_value = os.getenv(env_var)
                if env_value:
                    config[key] = env_value
                else:
                    self.logger.warning(f"Environment variable {env_var} not found")
    
    def validate_config(self) -> bool:
        """Validate configuration."""
        errors = []
        
        # Check LLM backend
        if self.config.enable_llm:
            backend_config = self.get_llm_backend_config()
            if not backend_config:
                errors.append(f"No configuration for backend: {self.config.llm_backend_type}")
        
        # Check output format
        valid_formats = ["json", "sqlite", "both"]
        if self.config.output_format not in valid_formats:
            errors.append(f"Invalid output format: {self.config.output_format}")
        
        # Check numeric values
        if self.config.parallel_pages < 1:
            errors.append("parallel_pages must be >= 1")
        
        if self.config.confidence_threshold < 0 or self.config.confidence_threshold > 1:
            errors.append("confidence_threshold must be between 0 and 1")
        
        if errors:
            for error in errors:
                self.logger.error(f"Config validation error: {error}")
            return False
        
        return True
    
    def merge_with_cli_args(self, cli_args: Dict[str, Any]):
        """Merge CLI arguments with configuration."""
        # Create a copy of current config
        merged_config = deepcopy(self.config_dict)
        
        # Map CLI args to config structure
        if "backend" in cli_args:
            merged_config.setdefault("llm_backend", {})["type"] = cli_args["backend"]
        
        if "max_pages" in cli_args:
            merged_config.setdefault("pipeline", {})["max_pages"] = cli_args["max_pages"]
        
        if "parallel" in cli_args:
            merged_config.setdefault("pipeline", {})["parallel_pages"] = cli_args["parallel"]
        
        if "no_llm" in cli_args and cli_args["no_llm"]:
            merged_config.setdefault("pipeline", {})["enable_llm"] = False
        
        # Update config object
        self.config = SemanticPipelineConfig.from_dict(merged_config)
        
        return self.config