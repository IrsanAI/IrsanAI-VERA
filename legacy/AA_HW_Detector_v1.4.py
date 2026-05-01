# ================================================
# IrsanAI_OS_HW_Detector.py – LAPTOP / PYCHARM v1.4-desktop
# Für Windows, Linux, macOS – optimiert für PyCharm
# ================================================

import os
import platform
import sys
import json
import subprocess
import psutil
import datetime
from pathlib import Path
import warnings

warnings.filterwarnings("ignore", category=RuntimeWarning)


def detect_os():
    return {
        "os": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "architecture": platform.machine(),
        "processor": platform.processor(),
        "platform": platform.platform(),
        "pycharm_detected": "PYCHARM_HOSTED" in os.environ or "idea" in sys.executable.lower()
    }


def detect_cpu():
    try:
        return {
            "cores_physical": psutil.cpu_count(logical=False),
            "cores_logical": psutil.cpu_count(logical=True),
            "frequency_current_mhz": round(psutil.cpu_freq().current, 2) if psutil.cpu_freq() else None,
            "frequency_max_mhz": round(psutil.cpu_freq().max, 2) if psutil.cpu_freq() else None,
            "usage_percent": psutil.cpu_percent(interval=1)
        }
    except:
        return {"error": "CPU-Daten nicht vollständig lesbar"}


def detect_memory():
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    return {
        "ram_total_gb": round(mem.total / (1024 ** 3), 2),
        "ram_available_gb": round(mem.available / (1024 ** 3), 2),
        "ram_used_gb": round(mem.used / (1024 ** 3), 2),
        "ram_percent": mem.percent,
        "swap_total_gb": round(swap.total / (1024 ** 3), 2)
    }


def detect_disk():
    disk = psutil.disk_usage('/')
    return {
        "disk_total_gb": round(disk.total / (1024 ** 3), 2),
        "disk_free_gb": round(disk.free / (1024 ** 3), 2),
        "disk_used_percent": disk.percent
    }


def detect_gpu():
    gpu_info = {"available": False, "details": []}
    # Torch CUDA
    try:
        import torch
        if torch.cuda.is_available():
            gpu_info["available"] = True
            for i in range(torch.cuda.device_count()):
                gpu_info["details"].append({
                    "type": "NVIDIA CUDA",
                    "device_id": i,
                    "name": torch.cuda.get_device_name(i),
                    "memory_total_gb": round(torch.cuda.get_device_properties(i).total_memory / (1024 ** 3), 2)
                })
    except:
        pass

    # NVIDIA-SMI Fallback
    if not gpu_info["available"]:
        try:
            result = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
                                    capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                gpu_info["available"] = True
                for line in result.stdout.strip().splitlines():
                    if ',' in line:
                        name, mem = line.split(',')
                        gpu_info["details"].append({
                            "type": "NVIDIA",
                            "name": name.strip(),
                            "memory_total_gb": round(float(mem.strip()) / 1024, 2)
                        })
        except:
            pass
    return gpu_info


def detect_python():
    return {
        "python_version": sys.version.split()[0],
        "executable": sys.executable,
        "pycharm": "PYCHARM_HOSTED" in os.environ
    }


def detect_network():
    try:
        import socket
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return {"internet": True}
    except:
        return {"internet": False}


def main():
    report = {
        "timestamp": datetime.datetime.now().isoformat(),
        "detector_version": "1.4-desktop",
        "task_id": "usr_1776123837045_0jhv30",
        "system": detect_os(),
        "cpu": detect_cpu(),
        "memory": detect_memory(),
        "disk": detect_disk(),
        "gpu": detect_gpu(),
        "python": detect_python(),
        "network": detect_network()
    }

    output_file = Path("IrsanAI_HW_Report.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print("✅ IrsanAI OS/HW DETECTOR v1.4-desktop – ERFOLGREICH ABGESCHLOSSEN")
    print("=" * 80)
    print(f"Zeitstempel     : {report['timestamp']}")
    print(
        f"Betriebssystem  : {report['system']['os']} {report['system']['release']} ({report['system']['architecture']})")
    print(
        f"CPU             : {report['cpu'].get('cores_logical', 'N/A')} Kerne @ {report['cpu'].get('frequency_current_mhz', 'N/A')} MHz")
    print(f"RAM verfügbar   : {report['memory']['ram_available_gb']} / {report['memory']['ram_total_gb']} GB")
    print(f"Speicher frei   : {report['disk']['disk_free_gb']} GB")
    print(
        f"GPU             : {'✓ ' + report['gpu']['details'][0]['name'] if report['gpu']['available'] else '✗ (keine dedizierte GPU erkannt)'}")
    print(f"Internet        : {'✓ Verbunden' if report['network']['internet'] else '✗'}")
    print(f"PyCharm erkannt : {'Ja' if report['system']['pycharm_detected'] else 'Nein'}")
    print(f"Report gespeichert: {output_file.absolute()}")
    print("=" * 80)
    print("✅ Detektor läuft jetzt perfekt auf deinem Laptop mit PyCharm!")
    print("   Schick mir bitte die komplette Ausgabe + cat IrsanAI_HW_Report.json")
    print("=" * 80)


if __name__ == "__main__":
    # Abhängigkeiten prüfen
    try:
        import psutil
    except ImportError:
        print("⚠️ psutil fehlt → pip install psutil")
        sys.exit(1)
    main()