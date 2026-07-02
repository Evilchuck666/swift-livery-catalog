#!/usr/bin/env python3
"""
Espejo automático del proyecto ENTERO a un 2º servidor FTP (copia EXACTA).

El plugin de VSCode (Natizyskunk.sftp) solo puede auto-subir al profile ACTIVO,
así que no puede mantener dos servidores en sync a la vez. Este script cubre ese
hueco: vigila el proyecto y replica TODO (incluidos .git/ y .vscode/) al servidor
definido en el profile "backup" de .vscode/sftp.json.

Sin dependencias externas: solo la librería estándar (os.walk + mtime/size para
detectar cambios, ftplib para subir).

Uso:
  python3 resources/scripts/deploy-mirror.py            # vigila y replica en bucle
  python3 resources/scripts/deploy-mirror.py --once     # un único pase completo y sale
  python3 resources/scripts/deploy-mirror.py --delete   # espejo estricto: borra en remoto lo que no exista en local
  python3 resources/scripts/deploy-mirror.py --profile backup --interval 2

Notas:
  - Lee host/usuario/contraseña/remotePath del profile "backup" de sftp.json.
    Es la única fuente de credenciales (no se duplican aquí).
  - Sube ABSOLUTAMENTE TODO lo que haya bajo la raíz del proyecto. No aplica
    ningún ignore (es una copia exacta). El único elemento excluido es el propio
    directorio de trabajo temporal de nadie: nada.
"""

import argparse
import ftplib
import json
import os
import sys
import time

# ── Rutas ─────────────────────────────────────────────────────────────────────
# .../resources/scripts/deploy-mirror.py  ->  raíz del proyecto = ../../
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, os.pardir, os.pardir))
SFTP_JSON = os.path.join(PROJECT_ROOT, ".vscode", "sftp.json")


# ── Config ────────────────────────────────────────────────────────────────────
def load_profile(profile_name):
    """Devuelve (host, port, user, password, remote_path) del profile indicado."""
    with open(SFTP_JSON, encoding="utf-8") as f:
        cfg = json.load(f)

    profiles = cfg.get("profiles", {})
    if profile_name not in profiles:
        sys.exit(f"✗ El profile '{profile_name}' no existe en {SFTP_JSON}. "
                 f"Profiles disponibles: {', '.join(profiles) or '(ninguno)'}")

    prof = profiles[profile_name]
    # Herencia: el profile puede heredar valores de la raíz (como hace el plugin).
    def val(key, default=None):
        return prof.get(key, cfg.get(key, default))

    host = str(val("host", "")).replace("ftp://", "").replace("ftps://", "").rstrip("/")
    port = int(val("port", 21))
    user = val("username", "")
    password = val("password", "")
    remote_path = str(val("remotePath", "/")).rstrip("/") or "/"

    if not host or host.startswith("SERVIDOR2"):
        sys.exit(f"✗ Rellena los datos reales de '{profile_name}' en {SFTP_JSON} "
                 f"(host/username/password/remotePath).")
    return host, port, user, password, remote_path


# ── Escaneo local ─────────────────────────────────────────────────────────────
def scan_local():
    """Mapa {ruta_relativa_posix: (mtime, size)} de TODOS los archivos del proyecto."""
    files = {}
    for dirpath, dirnames, filenames in os.walk(PROJECT_ROOT):
        for name in filenames:
            full = os.path.join(dirpath, name)
            try:
                st = os.stat(full)
            except OSError:
                continue
            rel = os.path.relpath(full, PROJECT_ROOT).replace(os.sep, "/")
            files[rel] = (st.st_mtime, st.st_size)
    return files


# ── Cliente FTP ───────────────────────────────────────────────────────────────
class FtpMirror:
    def __init__(self, host, port, user, password, remote_root):
        self.host, self.port = host, port
        self.user, self.password = user, password
        self.remote_root = remote_root
        self.ftp = None
        self._known_dirs = set()

    def connect(self):
        self.ftp = ftplib.FTP()
        self.ftp.connect(self.host, self.port, timeout=30)
        self.ftp.login(self.user, self.password)
        self.ftp.set_pasv(True)
        self._known_dirs.clear()
        self._ensure_dir(self.remote_root)

    def close(self):
        if self.ftp:
            try:
                self.ftp.quit()
            except Exception:
                try:
                    self.ftp.close()
                except Exception:
                    pass
            self.ftp = None

    def _ensure_dir(self, remote_dir):
        """Crea el directorio remoto (y sus padres) si no existe."""
        if remote_dir in self._known_dirs or remote_dir in ("", "/"):
            return
        parts = remote_dir.strip("/").split("/")
        path = "" if self.remote_root.startswith("/") else "."
        if self.remote_root.startswith("/"):
            path = ""
        for p in parts:
            path = f"{path}/{p}" if path else ("/" + p if self.remote_root.startswith("/") else p)
            if path in self._known_dirs:
                continue
            try:
                self.ftp.mkd(path)
            except ftplib.error_perm as e:
                # 550 = ya existe (o sin permiso); asumimos que existe
                if not str(e).startswith("550"):
                    raise
            self._known_dirs.add(path)

    def remote_path_for(self, rel):
        return f"{self.remote_root}/{rel}"

    def upload(self, rel, local_full):
        remote = self.remote_path_for(rel)
        self._ensure_dir(remote.rsplit("/", 1)[0])
        with open(local_full, "rb") as fh:
            self.ftp.storbinary(f"STOR {remote}", fh)

    def delete(self, rel):
        remote = self.remote_path_for(rel)
        try:
            self.ftp.delete(remote)
        except ftplib.error_perm:
            pass


# ── Bucle principal ───────────────────────────────────────────────────────────
def sync_once(mirror, state, delete_removed):
    """Sube archivos nuevos/cambiados; opcionalmente borra los que ya no existen."""
    current = scan_local()
    uploaded = 0

    for rel, meta in sorted(current.items()):
        if state.get(rel) == meta:
            continue  # sin cambios
        local_full = os.path.join(PROJECT_ROOT, rel.replace("/", os.sep))
        try:
            mirror.upload(rel, local_full)
            state[rel] = meta
            uploaded += 1
            print(f"  ↑ {rel}")
        except Exception as e:
            print(f"  ! error subiendo {rel}: {e}")
            raise  # deja que el bucle exterior reconecte

    removed = 0
    if delete_removed:
        for rel in list(state.keys()):
            if rel not in current:
                mirror.delete(rel)
                state.pop(rel, None)
                removed += 1
                print(f"  ✗ borrado remoto {rel}")

    return uploaded, removed, len(current)


def main():
    ap = argparse.ArgumentParser(description="Espejo FTP completo a un 2º servidor.")
    ap.add_argument("--profile", default="backup", help="Profile de sftp.json (por defecto: backup)")
    ap.add_argument("--once", action="store_true", help="Un único pase completo y salir")
    ap.add_argument("--delete", action="store_true", help="Borrar en remoto lo que ya no exista en local (espejo estricto)")
    ap.add_argument("--interval", type=float, default=2.0, help="Segundos entre escaneos (por defecto: 2)")
    args = ap.parse_args()

    host, port, user, password, remote_root = load_profile(args.profile)
    print(f"→ Espejo a ftp://{host}:{port}{remote_root}  (profile '{args.profile}')")
    print(f"→ Raíz local: {PROJECT_ROOT}")
    if args.delete:
        print("→ Modo espejo estricto: se BORRARÁN en remoto los archivos eliminados en local.")

    mirror = FtpMirror(host, port, user, password, remote_root)
    state = {}

    def do_pass():
        up, rm, total = sync_once(mirror, state, args.delete)
        if up or rm:
            print(f"  ({up} subidos, {rm} borrados, {total} archivos en total)")
        return up, rm

    # Primer pase (completo)
    try:
        mirror.connect()
        print("Pase inicial…")
        do_pass()
        print("✓ Pase inicial completado.")
    except Exception as e:
        mirror.close()
        sys.exit(f"✗ No se pudo completar el pase inicial: {e}")

    if args.once:
        mirror.close()
        return

    print(f"Vigilando cambios cada {args.interval}s… (Ctrl-C para salir)")
    try:
        while True:
            time.sleep(args.interval)
            try:
                # keep-alive; reconecta si la conexión se cayó
                try:
                    mirror.ftp.voidcmd("NOOP")
                except Exception:
                    print("Reconectando…")
                    mirror.close()
                    mirror.connect()
                do_pass()
            except Exception as e:
                print(f"  ! error en el ciclo: {e} — reintentando…")
                mirror.close()
                try:
                    mirror.connect()
                except Exception as e2:
                    print(f"  ! sin conexión: {e2}")
    except KeyboardInterrupt:
        print("\nDetenido.")
    finally:
        mirror.close()


if __name__ == "__main__":
    main()
