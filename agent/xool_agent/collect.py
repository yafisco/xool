"""Collecte des mesures de la machine locale avec psutil."""

import os
import socket
import time
from datetime import UTC, datetime

import psutil

# Une mesure, au format attendu par `POST /metrics`.
Measure = dict[str, str | float | bool | None]

# Mêmes bornes que l'API : une valeur aberrante ferait refuser tout le lot (422).
TEMPERATURE_MIN = -50.0
TEMPERATURE_MAX = 150.0

# Capteurs du processeur selon le matériel (Intel, AMD, Raspberry Pi, ACPI), par préférence.
CPU_SENSORS = ("coretemp", "k10temp", "zenpower", "cpu_thermal", "acpitz")


def system_disk_path() -> str:
    """Racine du disque système : `C:\\` sous Windows, `/` ailleurs."""
    if os.name == "nt":
        # Variable SystemDrive de Windows (les noms de variables n'y ont pas de casse).
        return os.environ.get("SYSTEMDRIVE", "C:") + "\\"
    return "/"


def read_temperature() -> float | None:
    """Température du processeur en °C, ou None si la machine ne l'expose pas."""
    # psutil ne fournit cette fonction que sous Linux et FreeBSD : elle n'existe pas sous Windows.
    read_sensors = getattr(psutil, "sensors_temperatures", None)
    if read_sensors is None:
        return None
    try:
        sensors = read_sensors()
    except OSError:
        return None

    # Les capteurs connus du processeur d'abord, puis n'importe quel autre capteur.
    for name in (*CPU_SENSORS, *sensors):
        values = [
            reading.current
            for reading in sensors.get(name, [])
            if TEMPERATURE_MIN <= reading.current <= TEMPERATURE_MAX
        ]
        if values:
            return round(max(values), 1)
    return None


def _percent(value: float) -> float:
    return round(min(100.0, max(0.0, value)), 1)


def collect(cpu_interval: float | None = None) -> Measure:
    """Mesure l'état de la machine à cet instant.

    `cpu_interval=None` : charge CPU moyenne depuis l'appel précédent, sans attendre (la toute
    première fois, psutil n'a pas de point de comparaison et renvoie 0).
    `cpu_interval=1.0` : attend une seconde et mesure la charge pendant cette seconde.
    """
    return {
        "hostname": socket.gethostname()[:255] or "inconnu",
        # Toujours en UTC, à la seconde : l'heure de Dakar ne sert qu'à l'affichage.
        "time": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "cpu": _percent(psutil.cpu_percent(interval=cpu_interval)),
        "ram": _percent(psutil.virtual_memory().percent),
        "disk": _percent(psutil.disk_usage(system_disk_path()).percent),
        "temperature": read_temperature(),
        "uptime_h": round(max(0.0, time.time() - psutil.boot_time()) / 3600, 2),
        "online": True,
    }
