from typing import List
from dataclasses import dataclass
import yaml
from pydantic import BaseModel, validator


class Server(BaseModel):
    name: str
    ip: str
    port: int
    login: str
    password: str
    backup_filename: str
    backup_interval: int


class BackupSettings(BaseModel):
    local: bool
    auto: str  # HH:MM format
    format: str

    @validator("auto")
    def valid_time_format(cls, v):
        if len(v.split(":")) != 2:
            raise ValueError("auto must be in HH:MM format")
        h, m = v.split(":")
        if not (0 <= int(h) < 24 and 0 <= int(m) < 60):
            raise ValueError("auto time must be valid 24-hour time")
        return v


class BotSettings(BaseModel):
    token: str
    admin_id: List[int]


@dataclass
class Config:
    bot: BotSettings
    servers: List[Server]
    backup: BackupSettings


def load_config() -> Config:
    with open("config.yml", "r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
    bot = BotSettings(**data.get("bot", {}))
    servers = [Server(**srv) for srv in data.get("servers", [])]
    backup = BackupSettings(**data.get("backup", {}))
    return Config(bot=bot, servers=servers, backup=backup)


config = load_config()

