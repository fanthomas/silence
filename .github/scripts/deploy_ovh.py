#!/usr/bin/env python3
"""Déploiement SFTP limité à l'application silence. Aucun fichier distant supprimé."""
import os
import pathlib
import sys
import tempfile
import paramiko

HOST = "ftp.cluster111.hosting.ovh.net"
USER = "zmmenuisfa-silence"
FILES = (
    "index.html",
    "styles.css",
    "app.js",
    "sw.js",
    "manifest.webmanifest",
    "icons/icon-192.png",
    "icons/icon-512.png",
)
mode = sys.argv[1] if len(sys.argv) > 1 else "verify"
if mode not in ("verify", "deploy"):
    raise SystemExit("Mode non autorisé")
if os.environ.get("OVH_SFTP_HOST") != HOST or os.environ.get("OVH_SFTP_USER") != USER:
    raise SystemExit("Accès OVH non conforme au compte restreint")
password = os.environ.get("OVH_SFTP_PASSWORD", "")
known_hosts = os.environ.get("OVH_SFTP_KNOWN_HOSTS", "")
if not known_hosts.strip():
    known_hosts = pathlib.Path(".github/ovh_known_hosts").read_text(encoding="utf-8")
if not password or not known_hosts.strip():
    raise SystemExit("Mot de passe SFTP ou clé publique OVH manquant")
base = pathlib.Path("meditation")
if mode == "deploy" and any(not (base / name).is_file() for name in FILES):
    raise SystemExit("Fichiers application incomplets : publication annulée")

with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8") as f:
    f.write(known_hosts.rstrip("\n") + "\n")
    f.flush()
    client = paramiko.SSHClient()
    client.load_host_keys(f.name)
    client.set_missing_host_key_policy(paramiko.RejectPolicy())
    try:
        client.connect(
            HOST, port=22, username=USER, password=password,
            look_for_keys=False, allow_agent=False, timeout=25, auth_timeout=25,
        )
        with client.open_sftp() as sftp:
            print("Connexion SFTP vérifiée. Répertoire autorisé :", sftp.normalize("."))
            if mode == "verify":
                print("MODE VÉRIFICATION : aucun fichier envoyé.")
            else:
                try:
                    sftp.stat("icons")
                except FileNotFoundError:
                    sftp.mkdir("icons")
                for rel in FILES:
                    sftp.put(str(base / rel), rel, confirm=True)
                    print("Publié :", rel)
                print("Déploiement terminé (sans suppression distante).")
    finally:
        client.close()
