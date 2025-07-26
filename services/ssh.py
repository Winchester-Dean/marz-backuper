import os
import paramiko
import logging
import stat
import shutil
from pathlib import Path
from typing import List
from config_reader import config

logger = logging.getLogger(__name__)

class SSHClient:
    def __init__(self, server):
        self.server = server
        self.ssh = None

    def connect(self):
        if self.server.ip.lower() == "local":
            return None
        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(
                self.server.ip,
                port=self.server.port,
                username=self.server.login,
                password=self.server.password,
                timeout=10,
            )
            return self.ssh
        except Exception as e:
            logger.error(f"Ошибка SSH подключения к серверу {self.server.name}: {e}", exc_info=True)
            raise

    def download_dirs(self, remote_dirs: List[str], local_dir: Path):
        """
        Скачивает несколько директорий.
        Формирует структуру внутри local_dir в формате:
        marzban/var/lib/marzban
        marzban/opt/marzban
        """
        local_dir.mkdir(parents=True, exist_ok=True)
        ROOT_NAME = "marzban"  # корневая папка, внутри которой будет структура

        if self.server.ip.lower() == "local":
            try:
                root_local = local_dir / ROOT_NAME
                if root_local.exists():
                    shutil.rmtree(root_local)
                root_local.mkdir(parents=True)
                for rdir in remote_dirs:
                    p = Path(rdir)
                    # Путь относительно корня файловой системы "/"
                    relative_path = p.relative_to("/")
                    target_dir = root_local / relative_path.parent
                    target_dir.mkdir(parents=True, exist_ok=True)
                    # Копируем содержимое rdir в соответствующую папку в tmp/marzban/...
                    shutil.copytree(rdir, target_dir / p.name, dirs_exist_ok=True)
            except Exception as e:
                logger.error(f"Ошибка копирования локальных файлов: {e}", exc_info=True)
                raise
            return

        # Для ssh-сервера
        try:
            self.connect()
            if not self.ssh:
                logger.error(f"SSH не подключен к серверу {self.server.name}")
                return
            sftp = self.ssh.open_sftp()
            try:
                root_local = local_dir / ROOT_NAME
                if root_local.exists():
                    shutil.rmtree(root_local)
                root_local.mkdir(parents=True)
                for rdir in remote_dirs:
                    p = Path(rdir)
                    relative_path = p.relative_to("/")
                    local_target = root_local / relative_path.parent
                    local_target.mkdir(parents=True, exist_ok=True)
                    self._download_recursive(sftp, rdir, local_target / p.name)
            except Exception as e:
                logger.error(f"Ошибка скачивания директорий {remote_dirs} с сервера {self.server.name}: {e}", exc_info=True)
                raise
            finally:
                sftp.close()
                self.ssh.close()
        except Exception as e:
            logger.error(f"Ошибка в SSH клиенте при скачивании директорий: {e}", exc_info=True)
            raise

    def _download_recursive(self, sftp, remote_path, local_path):
        local_path.mkdir(parents=True, exist_ok=True)
        try:
            for f in sftp.listdir_attr(remote_path):
                remote_item = f"{remote_path}/{f.filename}"
                local_item = local_path / f.filename
                if self._is_dir(sftp, remote_item):
                    self._download_recursive(sftp, remote_item, local_item)
                else:
                    sftp.get(remote_item, str(local_item))
        except Exception as e:
            logger.error(f"Ошибка рекурсивного скачивания с {remote_path} на {local_path}: {e}", exc_info=True)
            raise

    @staticmethod
    def _is_dir(sftp, path):
        try:
            return stat.S_ISDIR(sftp.stat(path).st_mode)
        except IOError:
            return False

