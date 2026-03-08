import json
import os


class RecentFiles:
    """
    Gestiona la lista de archivos recientes.
    Se guarda en %APPDATA%/ExamBox/recent.json (Windows).
    """

    MAX_FILES = 5

    def __init__(self):
        self._path = self._config_path()
        self._files: list[str] = self._load()

    def add(self, path: str):
        """Añade un archivo a la lista, eliminando duplicados y manteniendo el límite."""
        path = os.path.normpath(path)
        if path in self._files:
            self._files.remove(path)
        self._files.insert(0, path)
        self._files = self._files[:self.MAX_FILES]
        self._save()

    def get_all(self) -> list[str]:
        """Devuelve los archivos recientes que aún existen en disco."""
        self._files = [f for f in self._files if os.path.exists(f)]
        return list(self._files)

    def clear(self):
        self._files = []
        self._save()

    # ------------------------------------------------------------------ #
    #  Persistencia
    # ------------------------------------------------------------------ #

    @staticmethod
    def _config_path() -> str:
        appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
        folder = os.path.join(appdata, "ExamBox")
        os.makedirs(folder, exist_ok=True)
        return os.path.join(folder, "recent.json")

    def _load(self) -> list[str]:
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save(self):
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(self._files, f, ensure_ascii=False, indent=2)
        except Exception:
            pass