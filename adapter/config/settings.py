"""
Configuration settings for Gun Registry Adapter.

Loads environment variables from .env file.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # =================================================================
    # API Keys (REQUIRED)
    # =================================================================
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    anthropic_api_key: str = Field(..., env="ANTHROPIC_API_KEY")

    # =================================================================
    # Model A (Perception/OCR) Configuration
    # =================================================================
    model_a_confidence_threshold: float = Field(0.8, env="MODEL_A_CONFIDENCE_THRESHOLD")
    image_quality_threshold: float = Field(0.5, env="IMAGE_QUALITY_THRESHOLD")
    enable_tamper_detection: bool = Field(True, env="ENABLE_TAMPER_DETECTION")

    # =================================================================
    # Model B (Reasoning) Configuration
    # =================================================================
    model_b_risk_threshold: float = Field(0.7, env="MODEL_B_RISK_THRESHOLD")
    linkage_confidence_threshold: float = Field(0.7, env="LINKAGE_CONFIDENCE_THRESHOLD")
    linkage_manual_review_min: float = Field(0.7, env="LINKAGE_MANUAL_REVIEW_MIN")
    linkage_manual_review_max: float = Field(0.9, env="LINKAGE_MANUAL_REVIEW_MAX")

    openai_model: str = Field("gpt-4o-mini", env="OPENAI_MODEL")
    openai_temperature: float = Field(0.0, env="OPENAI_TEMPERATURE")
    openai_max_tokens: int = Field(1000, env="OPENAI_MAX_TOKENS")

    # =================================================================
    # Model C (Self-Healing) Configuration
    # =================================================================
    self_healing_enabled: bool = Field(True, env="SELF_HEALING_ENABLED")
    auto_apply_fixes: bool = Field(False, env="AUTO_APPLY_FIXES")
    self_healing_confidence_threshold: float = Field(0.9, env="SELF_HEALING_CONFIDENCE_THRESHOLD")

    claude_model: str = Field("claude-sonnet-4-5-20250929", env="CLAUDE_MODEL")
    claude_max_tokens: int = Field(4000, env="CLAUDE_MAX_TOKENS")
    claude_temperature: float = Field(0.0, env="CLAUDE_TEMPERATURE")

    # =================================================================
    # Database Configuration
    # =================================================================
    database_path: str = Field("data/registry.db", env="DATABASE_PATH")
    self_healing_db_path: str = Field("data/self_healing.db", env="SELF_HEALING_DB_PATH")
    database_encryption_enabled: bool = Field(False, env="DATABASE_ENCRYPTION_ENABLED")

    # =================================================================
    # n8n Integration
    # =================================================================
    n8n_webhook_url: str = Field("http://localhost:5678/webhook/eligibility", env="N8N_WEBHOOK_URL")
    n8n_basic_auth_user: str = Field("admin", env="N8N_BASIC_AUTH_USER")
    n8n_basic_auth_password: str = Field("changeme", env="N8N_BASIC_AUTH_PASSWORD")
    n8n_instance_url: str = Field("http://localhost:5678", env="N8N_INSTANCE_URL")

    # =================================================================
    # API Server Configuration
    # =================================================================
    api_host: str = Field("0.0.0.0", env="API_HOST")
    api_port: int = Field(8000, env="API_PORT")
    api_workers: int = Field(2, env="API_WORKERS")
    api_cors_origins: str = Field("http://localhost:3000,http://localhost:5678", env="API_CORS_ORIGINS")
    api_rate_limit: int = Field(100, env="API_RATE_LIMIT")

    # =================================================================
    # Logging Configuration
    # =================================================================
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_pii: bool = Field(False, env="LOG_PII")
    log_file_path: str = Field("logs/audit.log", env="LOG_FILE_PATH")
    log_format: str = Field("json", env="LOG_FORMAT")
    log_console: bool = Field(True, env="LOG_CONSOLE")

    # =================================================================
    # Testing & Development
    # =================================================================
    test_mode: bool = Field(False, env="TEST_MODE")
    use_synthetic_nics: bool = Field(True, env="USE_SYNTHETIC_NICS")
    synthetic_nics_path: str = Field("data/processed/synthetic_nics_records.json", env="SYNTHETIC_NICS_PATH")
    debug: bool = Field(False, env="DEBUG")

    # =================================================================
    # Data Paths
    # =================================================================
    raw_data_path: str = Field("data/raw", env="RAW_DATA_PATH")
    processed_data_path: str = Field("data/processed", env="PROCESSED_DATA_PATH")
    synthetic_cards_path: str = Field("data/raw/synthetic_cards", env="SYNTHETIC_CARDS_PATH")
    nics_data_path: str = Field("data/raw/nics_data/nics-firearm-background-checks.csv", env="NICS_DATA_PATH")

    # =================================================================
    # Security & Privacy
    # =================================================================
    enable_pii_hashing: bool = Field(True, env="ENABLE_PII_HASHING")
    audit_log_retention_days: int = Field(2555, env="AUDIT_LOG_RETENTION_DAYS")  # 7 years
    enable_encryption: bool = Field(False, env="ENABLE_ENCRYPTION")
    secret_key: Optional[str] = Field(None, env="SECRET_KEY")

    # =================================================================
    # Feature Flags
    # =================================================================
    enable_model_a: bool = Field(True, env="ENABLE_MODEL_A")
    enable_model_b: bool = Field(True, env="ENABLE_MODEL_B")
    enable_model_c: bool = Field(True, env="ENABLE_MODEL_C")
    enable_linkage: bool = Field(True, env="ENABLE_LINKAGE")
    enable_metrics: bool = Field(True, env="ENABLE_METRICS")
    enable_health_check: bool = Field(True, env="ENABLE_HEALTH_CHECK")

    # =================================================================
    # Performance & Optimization
    # =================================================================
    ocr_timeout_seconds: int = Field(30, env="OCR_TIMEOUT_SECONDS")
    api_request_timeout: int = Field(60, env="API_REQUEST_TIMEOUT")
    cache_ttl_seconds: int = Field(3600, env="CACHE_TTL_SECONDS")
    enable_caching: bool = Field(False, env="ENABLE_CACHING")
    max_file_upload_size_mb: int = Field(10, env="MAX_FILE_UPLOAD_SIZE_MB")

    # =================================================================
    # Monitoring & Observability
    # =================================================================
    enable_prometheus: bool = Field(False, env="ENABLE_PROMETHEUS")
    prometheus_port: int = Field(9090, env="PROMETHEUS_PORT")
    enable_apm: bool = Field(False, env="ENABLE_APM")
    sentry_dsn: Optional[str] = Field(None, env="SENTRY_DSN")

    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "protected_namespaces": (),  # Allow fields starting with "model_"
        "extra": "ignore"  # Ignore extra fields in .env not defined in Settings
    }


# Singleton settings instance
settings = Settings()
