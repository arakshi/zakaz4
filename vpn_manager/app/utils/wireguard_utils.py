import base64
import os
import shutil
import subprocess


def _random_key() -> str:
    return base64.b64encode(os.urandom(32)).decode()


def generate_wg_keypair() -> tuple[str, str]:
    """Generate WireGuard keypair via `wg` if available, else fallback pseudo-keys for demo."""
    if shutil.which("wg"):
        private_key = subprocess.check_output(["wg", "genkey"], text=True).strip()
        public_key = subprocess.check_output(["bash", "-lc", f"echo '{private_key}' | wg pubkey"], text=True).strip()
        return private_key, public_key
    private = _random_key()
    public = _random_key()
    return private, public


def generate_preshared_key() -> str:
    if shutil.which("wg"):
        return subprocess.check_output(["wg", "genpsk"], text=True).strip()
    return _random_key()
