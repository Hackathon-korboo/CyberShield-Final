"""Centralized application settings management using Pydantic Settings.

Reads configuration from environment variables and `.env` files with strict type
validation, safe defaults, and secret masking.
"""

from functools import lru_cache
from typing import Any, List, Optional, Union
from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from backend.app.core.security import mask_secret


class Settings(BaseSettings):
    """Application settings schema for CyberShield AI 2.0."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Core Application Attributes
    app_name: str = Field("CyberShield AI 2.0", description="Display name of the application.")
    app_version: str = Field("2.0.0", description="Semantic application version.")
    environment: str = Field("development", description="Execution environment: development, staging, production.")
    debug: bool = Field(False, description="Debug mode flag.")

    # Server Binding
    host: str = Field("127.0.0.1", description="Host interface to bind server.")
    port: int = Field(8000, ge=1024, le=65535, description="Port to bind server.")

    # API Routing
    api_v1_str: str = Field("/api/v1", description="Prefix for API version 1 endpoints.")

    # CORS Configuration
    cors_origins: Union[List[str], str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
            "*",
        ],
        description="Allowed CORS origins for cross-origin frontend requests.",
    )

    # Security & Logging
    log_level: str = Field("INFO", description="Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL.")
    secret_key: SecretStr = Field(
        default=SecretStr("cybershield-insecure-dev-key-change-in-production-123456"),
        description="Internal application signing key.",
    )

    # AI Integration Subsystem (Google Gemini) - Phase 03 placeholder
    gemini_api_key: Optional[SecretStr] = Field(
        default=None,
        description="Google Gemini API Key for semantic social engineering analysis.",
    )
    gemini_model_name: str = Field(
        default="gemini-1.5-flash",
        description="Gemini model variant for threat analysis.",
    )
    ai_analysis_enabled: bool = Field(
        default=True,
        description="Toggle to enable or disable AI-assisted analysis.",
    )

    # Blockchain / Web3 Subsystem - Phase 04 placeholder
    web3_provider_uri: Optional[SecretStr] = Field(
        default=None,
        description="JSON-RPC HTTP/WSS endpoint for Ethereum/EVM node.",
    )
    blockchain_verification_enabled: bool = Field(
        default=False,
        description="Toggle to enable or disable Web3 trust registry verification.",
    )

    # Heuristic Engine Configuration - Phase 02 placeholder
    max_redirects: int = Field(5, ge=0, le=20, description="Max redirects to follow during deep URL inspection.")
    request_timeout_seconds: float = Field(5.0, ge=0.5, le=30.0, description="Network timeout for external requests.")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        """Support strings, wildcard, or comma-separated lists for CORS_ORIGINS."""
        if isinstance(v, str):
            clean_v = v.strip()
            if not clean_v or clean_v == "*":
                return ["*"]
            if clean_v.startswith("[") and clean_v.endswith("]"):
                import json
                try:
                    parsed = json.loads(clean_v)
                    if isinstance(parsed, list):
                        return [str(i).strip() for i in parsed if str(i).strip()]
                except Exception:
                    pass
            return [i.strip() for i in clean_v.split(",") if i.strip()]
        elif isinstance(v, (list, tuple, set)):
            return [str(i).strip() for i in v if str(i).strip()]
        return ["*"]

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Ensure environment is one of the permitted environments."""
        allowed = {"development", "testing", "staging", "production"}
        v_clean = v.strip().lower()
        if v_clean not in allowed:
            raise ValueError(f"Environment must be one of {allowed}, got '{v}'")
        return v_clean

    def get_masked_summary(self) -> dict:
        """Return a diagnostic summary of configuration with all secrets strictly masked."""
        return {
            "app_name": self.app_name,
            "app_version": self.app_version,
            "environment": self.environment,
            "debug": self.debug,
            "host": self.host,
            "port": self.port,
            "api_v1_str": self.api_v1_str,
            "cors_origins": self.cors_origins,
            "log_level": self.log_level,
            "secret_key": mask_secret(self.secret_key.get_secret_value() if self.secret_key else None),
            "gemini_api_key": mask_secret(self.gemini_api_key.get_secret_value() if self.gemini_api_key else None),
            "gemini_model_name": self.gemini_model_name,
            "ai_analysis_enabled": self.ai_analysis_enabled,
            "web3_provider_uri": mask_secret(self.web3_provider_uri.get_secret_value() if self.web3_provider_uri else None),
            "blockchain_verification_enabled": self.blockchain_verification_enabled,
        }


@lru_cache
def get_settings() -> Settings:
    """Cached singleton provider for application settings."""
    return Settings()
