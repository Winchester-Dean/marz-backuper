import os
import shutil
import datetime as dt
from pathlib import Path
import zipfile
import tarfile
import logging
from typing import Optional
from config_reader import config
from services.ssh import SSHClient

logger = logging.getLogger(__name__)

class Backuper:
    def __init__(self):
        self.backup_dir = Path("tmp")
        self.backup_dir.mkdir(exist_ok=True)

    def generate_backup_name(self, server_name: str) -> str:
        now = dt.datetime.now(dt.timezone(dt.timedelta(hours=3)))  # МСК
        stamp = now.strftime("%d-%m-%Y_%H-%M")
        fmt = config.backup.format.lower()
        ext = "tar.gz" if fmt == "tar.gz" else "zip"
        return f"{server_name}_{stamp}.{ext}"

    def create_backup(self, server, save_local: Optional[bool] = True) -> Path:
        try:
            archive_name = self.generate_backup_name(server.name)
            archive_path = self.backup_dir / archive_name

            tmp_dir = self.backup_dir / f"tmp_{server.name}"
            if tmp_dir.exists():
                shutil.rmtree(tmp_dir)
            tmp_dir.mkdir(parents=True)

            ssh_client = SSHClient(server)
            ssh_client.download_dirs(["/var/lib/marzban/", "/opt/marzban/"], tmp_dir)

            fmt = config.backup.format.lower()
            if fmt == "zip":
                with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
                    for root, _, files in os.walk(tmp_dir):
                        for file in files:
                            full_path = Path(root) / file
                            zf.write(full_path, arcname=full_path.relative_to(tmp_dir))
            elif fmt == "tar.gz":
                with tarfile.open(archive_path, "w:gz") as tar:
                    for root, dirs, files in os.walk(tmp_dir):
                        for file in files:
                            full_path = Path(root) / file
                            arcname = full_path.relative_to(tmp_dir)
                            tar.add(full_path, arcname=arcname)
            else:
                raise ValueError(f"Unsupported backup format: {config.backup.format}")

            shutil.rmtree(tmp_dir)

            if not save_local:
                return archive_path

            self._cleanup_old_backups(server.name)
            return archive_path

        except Exception as e:
            logger.error(f"Ошибка при создании резервной копии сервера {server.name}: {e}", exc_info=True)
            raise RuntimeError(f"Не удалось создать резервную копию для сервера {server.name}. Ошибка: {e}")

    def _cleanup_old_backups(self, server_name: str):
        try:
            fmt = config.backup.format.lower()
            ext = "tar.gz" if fmt == "tar.gz" else "zip"
            backups = sorted(
                self.backup_dir.glob(f"{server_name}_*.{ext}"),
                key=lambda x: x.stat().st_mtime,
            )
            while len(backups) > 3:
                oldest = backups.pop(0)
                oldest.unlink()
        except Exception as e:
            logger.error(f"Ошибка при очистке старых бэкапов: {e}", exc_info=True)

    def cleanup_all_backups(self) -> list[str]:
        try:
            fmt = config.backup.format.lower()
            ext = "tar.gz" if fmt == "tar.gz" else "zip"
            backups = list(self.backup_dir.glob(f"*.{ext}"))
            names = [b.name for b in backups]
            for b in backups:
                b.unlink()
            return names
        except Exception as e:
            logger.error(f"Ошибка при удалении всех бэкапов: {e}", exc_info=True)
            return []

backuper = Backuper()

