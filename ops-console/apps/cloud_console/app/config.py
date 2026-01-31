"""
配置管理：从 .env 读取（pydantic-settings）。
DATABASE_URL 仅在此处生成，其他地方只引用。
"""
from urllib.parse import quote_plus

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # 应用
    app_name: str = "Clawdbot Console"
    debug: bool = False
    APP_ENV: str = "dev"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    # 管理端（MVP 最简登录）
    ADMIN_USER: str = "admin"
    ADMIN_PASSWORD: str = "changeme_admin_pass"
    admin_username: str = "admin"
    admin_password: str = "changeme_admin_pass"
    secret_key: str = "changeme_secret_key_for_session"

    # 数据库（仅此处拼 URL，其余地方引用 DATABASE_URL）
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "cloud_console"
    DB_USER: str = "root"
    DB_PASSWORD: str = "password"

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        user = quote_plus(self.DB_USER)
        password = quote_plus(self.DB_PASSWORD)
        return (
            f"mysql+pymysql://{user}:{password}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            f"?charset=utf8mb4"
        )

    # 节点鉴权（MVP 仅 project_a）
    PROJECT_KEY_DEFAULT: str = "project_a"
    NODE_TOKEN_PROJECT_A: str = "changeme_node_token_project_a"

    # Console 公网/内网访问地址，用于展示给 Agent 的 CONSOLE_BASE_URL
    CONSOLE_PUBLIC_URL: str = ""


settings = Settings()
