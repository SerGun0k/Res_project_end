"""
Скрипт загрузки реальных характеристик из открытых источников.

Источники:
  - GPU: dbgpu (TechPowerUp) — https://github.com/painebenjamin/dbgpu
  - CPU: cpu-spec-dataset (cpubenchmark.net) — https://github.com/felixsteinke/cpu-spec-dataset

Данные легальны для использования — собраны из публичных спецификаций производителей.
"""

import json
import os
import sys
import csv
import urllib.request
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# URL открытых датасетов
GPU_DB_URL = "https://raw.githubusercontent.com/mlco2/impact/master/data/gpus.csv"
CPU_DB_URL = "https://raw.githubusercontent.com/felixsteinke/cpu-spec-dataset/main/dataset/benchmark-cpus.csv"

# Фильтры для отбора актуальных моделей (2020+)
GPU_BRANDS = ["NVIDIA", "AMD", "Intel"]
CPU_BRANDS = ["AMD", "Intel"]
MIN_YEAR = 2020


def download_csv(url: str) -> list[dict]:
    """Скачивание и парсинг CSV"""
    print(f"  📥 Загрузка {url.split('/')[-1]}...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        text = resp.read().decode("utf-8")

    reader = csv.DictReader(text.splitlines())
    rows = list(reader)
    print(f"  ✅ Загружено {len(rows)} записей")
    return rows


def extract_brand_from_gpu_name(name: str) -> str:
    """Извлечение бренда из названия GPU"""
    name_upper = name.upper()
    if "INTEL" in name_upper or "ARC" in name_upper:
        return "Intel"
    elif "AMD" in name_upper or "RADEON" in name_upper or "RX " in name_upper:
        return "AMD"
    elif "NVIDIA" in name_upper or "GEFORCE" in name_upper or "RTX" in name_upper or "GTX" in name_upper or "QUADRO" in name_upper:
        return "NVIDIA"
    return "Unknown"


def is_consumer_gpu(name: str) -> bool:
    """Проверка что GPU потребительский (не дата-центровый)"""
    name_upper = name.upper()
    # Исключаем серверные/дата-центровые
    exclude = ["H100", "A100", "A10G", "V100", "P100", "K80", "QUADRO", "TESLA", "TITAN"]
    for exc in exclude:
        if exc in name_upper:
            return False
    return True


def filter_gpus(raw_gpus: list[dict]) -> list[dict]:
    """Фильтрация GPU: только потребительские NVIDIA/AMD/Intel"""
    filtered = []
    for gpu in raw_gpus:
        name = gpu.get("name", "")
        brand = gpu.get("manufacturer", "") or extract_brand_from_gpu_name(name)

        if brand not in GPU_BRANDS:
            continue

        if not is_consumer_gpu(name):
            continue

        # Извлекаем ключевые характеристики
        memory = gpu.get("memory", "")
        tdp = gpu.get("tdp_watts", "")

        # Парсинг памяти
        try:
            mem_gb = int(float(memory)) if memory else None
        except (ValueError, TypeError):
            mem_gb = None

        # Парсинг TDP
        try:
            tdp_val = int(float(tdp)) if tdp else None
        except (ValueError, TypeError):
            tdp_val = None

        # Определяем тип памяти по названию
        mem_type = ""
        if "GDDR6X" in name.upper():
            mem_type = "GDDR6X"
        elif "GDDR6" in name.upper():
            mem_type = "GDDR6"
        elif "GDDR5" in name.upper():
            mem_type = "GDDR5"
        elif "HBM" in name.upper():
            mem_type = "HBM2"

        # Парсинг года из названия (если есть)
        year = 0
        if "RTX 40" in name.upper() or "RX 7" in name.upper():
            year = 2022
        elif "RTX 30" in name.upper() or "RX 6" in name.upper():
            year = 2020
        elif "ARC" in name.upper() or "A770" in name.upper() or "A750" in name.upper() or "A580" in name.upper():
            year = 2022
        elif "RTX 20" in name.upper() or "GTX 16" in name.upper() or "RX 5" in name.upper():
            year = 2019

        if year < MIN_YEAR:
            continue

        specs = {
            "memory_gb": mem_gb,
            "memory_type": mem_type,
            "tdp_watts": tdp_val,
            "release_date": f"{year}-01-01" if year >= MIN_YEAR else None,
        }

        filtered.append({
            "brand": brand,
            "model": name,
            "specs": specs,
            "release_date": specs["release_date"],
        })

    print(f"  📊 Отфильтровано {len(filtered)} GPU (2020+, потребительские)")
    return filtered


def filter_cpus(raw_cpus: list[dict]) -> list[dict]:
    """Фильтрация CPU: только AMD и Intel, 2020+"""
    filtered = []
    for cpu in raw_cpus:
        name = cpu.get("CpuName", "").strip()

        # Определяем бренд
        if name.upper().startswith("AMD"):
            brand = "AMD"
        elif name.upper().startswith("INTEL"):
            brand = "Intel"
        else:
            continue

        # Парсинг года
        release = cpu.get("ReleaseDate", "").strip()
        try:
            # Формат "Q1 2021"
            year = int(release.split()[-1]) if release else 0
        except (ValueError, IndexError):
            year = 0

        if year < MIN_YEAR:
            continue

        # Извлечение характеристик (безопасный парсинг)
        def safe_int(val):
            try:
                return int(float(str(val).strip().replace(" W", "")))
            except (ValueError, TypeError):
                return None

        def safe_float(val):
            try:
                return float(str(val).strip().replace(" GHz", ""))
            except (ValueError, TypeError):
                return None

        cores = safe_int(cpu.get("Cores"))
        threads = safe_int(cpu.get("Threads"))
        clock = safe_float(cpu.get("ClockSpeed"))
        turbo = safe_float(cpu.get("TurboSpeed"))
        tdp = safe_int(cpu.get("TDP"))

        specs = {
            "cores": cores,
            "threads": threads,
            "base_clock_ghz": clock,
            "boost_clock_ghz": turbo,
            "tdp_watts": tdp,
            "socket": cpu.get("Socket", ""),
            "release_date": release if release else None,
        }

        filtered.append({
            "brand": brand,
            "model": name,
            "specs": specs,
            "release_date": release if release else None,
        })

    print(f"  📊 Отфильтровано {len(filtered)} CPU (2020+, {', '.join(CPU_BRANDS)})")

    # Ограничиваем до 100 самых актуальных (последние модели каждого бренда)
    # Сортируем по году и берём топ
    def cpu_sort_key(cpu):
        release = cpu.get("release_date", "") or "Q1 2020"
        try:
            year = int(release.split()[-1])
            quarter = int(release.split()[0][-1])
        except (ValueError, IndexError):
            year, quarter = 2020, 1
        return (year, quarter)

    filtered.sort(key=cpu_sort_key, reverse=True)
    filtered = filtered[:100]
    print(f"  📝 Отобрано {len(filtered)} CPU (топ-100 по актуальности)")

    return filtered


def add_manual_data(items: list[dict]) -> list[dict]:
    """
    Добавление GPU, RAM, SSD, HDD, M.2 — для этих категорий
    реальные открытые датасеты с ценами не найдены.
    GPU добавлены из спецификаций NVIDIA/AMD (официальные документы).
    Остальные — из спецификаций производителей.
    """
    manual = [
        # GPU (из спецификаций NVIDIA/AMD, 2020+)
        {"category": "GPU", "brand": "NVIDIA", "model": "GeForce RTX 4090",
         "specs": {"memory_gb": 24, "memory_type": "GDDR6X", "tdp_watts": 450, "release_date": "2022-10-12"}},
        {"category": "GPU", "brand": "NVIDIA", "model": "GeForce RTX 4080",
         "specs": {"memory_gb": 16, "memory_type": "GDDR6X", "tdp_watts": 320, "release_date": "2022-11-16"}},
        {"category": "GPU", "brand": "NVIDIA", "model": "GeForce RTX 4070 Ti",
         "specs": {"memory_gb": 12, "memory_type": "GDDR6X", "tdp_watts": 285, "release_date": "2023-01-05"}},
        {"category": "GPU", "brand": "NVIDIA", "model": "GeForce RTX 4070",
         "specs": {"memory_gb": 12, "memory_type": "GDDR6X", "tdp_watts": 200, "release_date": "2023-04-13"}},
        {"category": "GPU", "brand": "NVIDIA", "model": "GeForce RTX 4060 Ti",
         "specs": {"memory_gb": 8, "memory_type": "GDDR6", "tdp_watts": 160, "release_date": "2023-05-24"}},
        {"category": "GPU", "brand": "NVIDIA", "model": "GeForce RTX 4060",
         "specs": {"memory_gb": 8, "memory_type": "GDDR6", "tdp_watts": 115, "release_date": "2023-06-29"}},
        {"category": "GPU", "brand": "NVIDIA", "model": "GeForce RTX 3080",
         "specs": {"memory_gb": 10, "memory_type": "GDDR6X", "tdp_watts": 320, "release_date": "2020-09-17"}},
        {"category": "GPU", "brand": "NVIDIA", "model": "GeForce RTX 3070",
         "specs": {"memory_gb": 8, "memory_type": "GDDR6", "tdp_watts": 220, "release_date": "2020-10-29"}},
        {"category": "GPU", "brand": "NVIDIA", "model": "GeForce RTX 3060",
         "specs": {"memory_gb": 12, "memory_type": "GDDR6", "tdp_watts": 170, "release_date": "2021-02-25"}},
        {"category": "GPU", "brand": "AMD", "model": "Radeon RX 7900 XTX",
         "specs": {"memory_gb": 24, "memory_type": "GDDR6", "tdp_watts": 355, "release_date": "2022-12-13"}},
        {"category": "GPU", "brand": "AMD", "model": "Radeon RX 7900 XT",
         "specs": {"memory_gb": 20, "memory_type": "GDDR6", "tdp_watts": 315, "release_date": "2022-12-13"}},
        {"category": "GPU", "brand": "AMD", "model": "Radeon RX 7800 XT",
         "specs": {"memory_gb": 16, "memory_type": "GDDR6", "tdp_watts": 263, "release_date": "2023-09-06"}},
        {"category": "GPU", "brand": "AMD", "model": "Radeon RX 7600",
         "specs": {"memory_gb": 8, "memory_type": "GDDR6", "tdp_watts": 165, "release_date": "2023-05-25"}},
        {"category": "GPU", "brand": "AMD", "model": "Radeon RX 6800 XT",
         "specs": {"memory_gb": 16, "memory_type": "GDDR6", "tdp_watts": 300, "release_date": "2020-11-18"}},
        {"category": "GPU", "brand": "AMD", "model": "Radeon RX 6700 XT",
         "specs": {"memory_gb": 12, "memory_type": "GDDR6", "tdp_watts": 230, "release_date": "2021-03-18"}},
        {"category": "GPU", "brand": "Intel", "model": "Arc A770 16GB",
         "specs": {"memory_gb": 16, "memory_type": "GDDR6", "tdp_watts": 225, "release_date": "2022-10-12"}},
        {"category": "GPU", "brand": "Intel", "model": "Arc A750",
         "specs": {"memory_gb": 8, "memory_type": "GDDR6", "tdp_watts": 225, "release_date": "2022-10-12"}},
        {"category": "GPU", "brand": "Intel", "model": "Arc A580",
         "specs": {"memory_gb": 8, "memory_type": "GDDR6", "tdp_watts": 185, "release_date": "2023-10-12"}},
        # RAM
        {"category": "RAM", "brand": "Corsair", "model": "Vengeance DDR5 32GB (2x16) 5600MHz",
         "specs": {"capacity_gb": 32, "type": "DDR5", "speed_mhz": 5600, "release_date": "2022-08-15"}},
        {"category": "RAM", "brand": "G.Skill", "model": "Trident Z5 DDR5 32GB (2x16) 6000MHz",
         "specs": {"capacity_gb": 32, "type": "DDR5", "speed_mhz": 6000, "release_date": "2022-09-20"}},
        {"category": "RAM", "brand": "Kingston", "model": "Fury Beast DDR5 16GB (2x8) 5200MHz",
         "specs": {"capacity_gb": 16, "type": "DDR5", "speed_mhz": 5200, "release_date": "2022-06-10"}},
        {"category": "RAM", "brand": "Corsair", "model": "Vengeance LPX DDR4 32GB (2x16) 3200MHz",
         "specs": {"capacity_gb": 32, "type": "DDR4", "speed_mhz": 3200, "release_date": "2019-03-15"}},
        {"category": "RAM", "brand": "G.Skill", "model": "Ripjaws V DDR4 16GB (2x8) 3600MHz",
         "specs": {"capacity_gb": 16, "type": "DDR4", "speed_mhz": 3600, "release_date": "2020-06-01"}},
        {"category": "RAM", "brand": "TeamGroup", "model": "T-Force Delta DDR5 32GB (2x16) 6400MHz",
         "specs": {"capacity_gb": 32, "type": "DDR5", "speed_mhz": 6400, "release_date": "2023-01-01"}},
        {"category": "RAM", "brand": "Crucial", "model": "Ballistix DDR4 32GB (2x16) 3600MHz",
         "specs": {"capacity_gb": 32, "type": "DDR4", "speed_mhz": 3600, "release_date": "2021-04-01"}},
        {"category": "RAM", "brand": "ADATA", "model": "XPG Spectrix DDR5 32GB (2x16) 6000MHz",
         "specs": {"capacity_gb": 32, "type": "DDR5", "speed_mhz": 6000, "release_date": "2023-03-01"}},
        # SSD
        {"category": "SSD", "brand": "Samsung", "model": "980 PRO 1TB NVMe",
         "specs": {"capacity_gb": 1000, "interface": "NVMe PCIe 4.0", "read_mbps": 7000, "write_mbps": 5000, "release_date": "2020-09-22"}},
        {"category": "SSD", "brand": "WD", "model": "Black SN850X 1TB NVMe",
         "specs": {"capacity_gb": 1000, "interface": "NVMe PCIe 4.0", "read_mbps": 7300, "write_mbps": 6300, "release_date": "2022-07-12"}},
        {"category": "SSD", "brand": "Crucial", "model": "P3 Plus 500GB NVMe",
         "specs": {"capacity_gb": 500, "interface": "NVMe PCIe 4.0", "read_mbps": 4700, "write_mbps": 1900, "release_date": "2022-05-18"}},
        {"category": "SSD", "brand": "Samsung", "model": "870 EVO 1TB SATA",
         "specs": {"capacity_gb": 1000, "interface": "SATA III", "read_mbps": 560, "write_mbps": 530, "release_date": "2021-01-20"}},
        {"category": "SSD", "brand": "Kingston", "model": "NV2 1TB NVMe",
         "specs": {"capacity_gb": 1000, "interface": "NVMe PCIe 4.0", "read_mbps": 3500, "write_mbps": 2100, "release_date": "2022-08-01"}},
        {"category": "SSD", "brand": "Samsung", "model": "970 EVO Plus 2TB NVMe",
         "specs": {"capacity_gb": 2000, "interface": "NVMe PCIe 3.0", "read_mbps": 3500, "write_mbps": 3300, "release_date": "2021-01-01"}},
        {"category": "SSD", "brand": "Seagate", "model": "FireCuda 530 1TB NVMe",
         "specs": {"capacity_gb": 1000, "interface": "NVMe PCIe 4.0", "read_mbps": 7300, "write_mbps": 6000, "release_date": "2021-08-01"}},
        {"category": "SSD", "brand": "SK Hynix", "model": "Platinum P41 2TB NVMe",
         "specs": {"capacity_gb": 2000, "interface": "NVMe PCIe 4.0", "read_mbps": 7000, "write_mbps": 6500, "release_date": "2022-08-01"}},
        # HDD
        {"category": "HDD", "brand": "Seagate", "model": "Barracuda 2TB 7200RPM",
         "specs": {"capacity_gb": 2000, "rpm": 7200, "cache_mb": 256, "interface": "SATA III", "release_date": "2020-06-15"}},
        {"category": "HDD", "brand": "WD", "model": "Blue 1TB 7200RPM",
         "specs": {"capacity_gb": 1000, "rpm": 7200, "cache_mb": 64, "interface": "SATA III", "release_date": "2019-11-10"}},
        {"category": "HDD", "brand": "Seagate", "model": "IronWolf 4TB NAS",
         "specs": {"capacity_gb": 4000, "rpm": 5900, "cache_mb": 256, "interface": "SATA III", "release_date": "2021-03-20"}},
        {"category": "HDD", "brand": "WD", "model": "Red Plus 4TB NAS",
         "specs": {"capacity_gb": 4000, "rpm": 5400, "cache_mb": 256, "interface": "SATA III", "release_date": "2021-06-01"}},
        {"category": "HDD", "brand": "Toshiba", "model": "X300 6TB 7200RPM",
         "specs": {"capacity_gb": 6000, "rpm": 7200, "cache_mb": 128, "interface": "SATA III", "release_date": "2022-03-01"}},
        {"category": "HDD", "brand": "WD", "model": "Black 2TB 7200RPM",
         "specs": {"capacity_gb": 2000, "rpm": 7200, "cache_mb": 256, "interface": "SATA III", "release_date": "2021-10-01"}},
        # M.2
        {"category": "M2", "brand": "Samsung", "model": "990 PRO 2TB M.2 NVMe",
         "specs": {"capacity_gb": 2000, "interface": "NVMe PCIe 4.0", "read_mbps": 7450, "write_mbps": 6900, "release_date": "2022-10-01"}},
        {"category": "M2", "brand": "WD", "model": "Black SN850X 2TB M.2 NVMe",
         "specs": {"capacity_gb": 2000, "interface": "NVMe PCIe 4.0", "read_mbps": 7300, "write_mbps": 6600, "release_date": "2022-07-12"}},
        {"category": "M2", "brand": "Kingston", "model": "KC3000 1TB M.2 NVMe",
         "specs": {"capacity_gb": 1000, "interface": "NVMe PCIe 4.0", "read_mbps": 7000, "write_mbps": 6000, "release_date": "2022-02-14"}},
        {"category": "M2", "brand": "Crucial", "model": "T500 1TB M.2 NVMe",
         "specs": {"capacity_gb": 1000, "interface": "NVMe PCIe 4.0", "read_mbps": 7400, "write_mbps": 7000, "release_date": "2023-02-01"}},
        {"category": "M2", "brand": "Samsung", "model": "980 500GB M.2 NVMe",
         "specs": {"capacity_gb": 500, "interface": "NVMe PCIe 3.0", "read_mbps": 3100, "write_mbps": 2600, "release_date": "2021-03-01"}},
        {"category": "M2", "brand": "WD", "model": "Blue SN570 1TB M.2 NVMe",
         "specs": {"capacity_gb": 1000, "interface": "NVMe PCIe 3.0", "read_mbps": 3500, "write_mbps": 3000, "release_date": "2021-06-01"}},
        {"category": "M2", "brand": "Seagate", "model": "FireCuda 520 2TB M.2 NVMe",
         "specs": {"capacity_gb": 2000, "interface": "NVMe PCIe 4.0", "read_mbps": 5000, "write_mbps": 4400, "release_date": "2021-01-01"}},
        # PSU (блоки питания)
        {"category": "PSU", "brand": "Corsair", "model": "RM850x 850W 80+ Gold",
         "specs": {"watts": 850, "efficiency": "80+ Gold", "modular": "Full", "release_date": "2021-06-01"}},
        {"category": "PSU", "brand": "Seasonic", "model": "FOCUS GX-750 750W 80+ Gold",
         "specs": {"watts": 750, "efficiency": "80+ Gold", "modular": "Full", "release_date": "2020-09-01"}},
        {"category": "PSU", "brand": "be quiet!", "model": "Dark Power 13 1000W 80+ Titanium",
         "specs": {"watts": 1000, "efficiency": "80+ Titanium", "modular": "Full", "release_date": "2022-11-01"}},
        {"category": "PSU", "brand": "EVGA", "model": "SuperNOVA 650 G6 650W 80+ Gold",
         "specs": {"watts": 650, "efficiency": "80+ Gold", "modular": "Full", "release_date": "2021-04-01"}},
        {"category": "PSU", "brand": "Corsair", "model": "CX650M 650W 80+ Bronze",
         "specs": {"watts": 650, "efficiency": "80+ Bronze", "modular": "Semi", "release_date": "2020-03-01"}},
        {"category": "PSU", "brand": "Thermaltake", "model": "Toughpower GF3 850W 80+ Gold",
         "specs": {"watts": 850, "efficiency": "80+ Gold", "modular": "Full", "release_date": "2022-10-01"}},
        {"category": "PSU", "brand": "Cooler Master", "model": "V850 SFX Gold 850W",
         "specs": {"watts": 850, "efficiency": "80+ Gold", "modular": "Full", "release_date": "2022-06-01"}},
        # Cooling
        {"category": "COOLING", "brand": "Noctua", "model": "NH-D15",
         "specs": {"type": "Air", "tdp_watts": 250, "noise_dba": 24.6, "release_date": "2020-01-01"}},
        {"category": "COOLING", "brand": "be quiet!", "model": "Dark Rock Pro 4",
         "specs": {"type": "Air", "tdp_watts": 250, "noise_dba": 24.3, "release_date": "2020-06-01"}},
        {"category": "COOLING", "brand": "Corsair", "model": "iCUE H150i Elite LCD XT",
         "specs": {"type": "AIO 360mm", "tdp_watts": 300, "noise_dba": 25, "release_date": "2022-09-01"}},
        {"category": "COOLING", "brand": "Arctic", "model": "Liquid Freezer II 280",
         "specs": {"type": "AIO 280mm", "tdp_watts": 280, "noise_dba": 22.5, "release_date": "2021-02-01"}},
        {"category": "COOLING", "brand": "Deepcool", "model": "AK620",
         "specs": {"type": "Air", "tdp_watts": 260, "noise_dba": 28, "release_date": "2022-01-01"}},
        {"category": "COOLING", "brand": "Noctua", "model": "NH-U12S chromax.black",
         "specs": {"type": "Air", "tdp_watts": 200, "noise_dba": 22.4, "release_date": "2020-09-01"}},
        {"category": "COOLING", "brand": "Corsair", "model": "iCUE H100i Elite LCD XT",
         "specs": {"type": "AIO 240mm", "tdp_watts": 250, "noise_dba": 24, "release_date": "2022-09-01"}},
    ]

    for item in manual:
        items.append({
            "category": item["category"],
            "brand": item["brand"],
            "model": item["model"],
            "specs": item["specs"],
            "release_date": item["specs"].get("release_date"),
        })

    print(f"  📝 Добавлено {len(manual)} товаров RAM/SSD/HDD/M.2 (спецификации производителей)")
    return items


def save_to_json(items: list[dict], filepath: str):
    """Сохранение в JSON формат"""
    # Группировка по категориям
    by_category = {}
    for item in items:
        cat = item.get("category", "GPU" if "memory_gb" in item.get("specs", {}) else "CPU")

        # Определяем категорию по наличию полей
        if "CpuName" in str(item) or "cores" in item.get("specs", {}):
            cat = "CPU"
        elif "memory_gb" in item.get("specs", {}):
            cat = "GPU"

        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(item)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(by_category, f, ensure_ascii=False, indent=2)

    total = sum(len(v) for v in by_category.values())
    print(f"\n💾 Сохранено {total} товаров в {filepath}")
    for cat, items in by_category.items():
        print(f"  {cat}: {len(items)}")


def main():
    print("=" * 60)
    print("📥 Загрузка реальных характеристик из открытых источников")
    print("=" * 60)

    all_items = []

    # GPU из dbgpu
    print("\n🎮 GPU (TechPowerUp via dbgpu)")
    try:
        raw_gpus = download_csv(GPU_DB_URL)
        gpus = filter_gpus(raw_gpus)
        for gpu in gpus:
            gpu["category"] = "GPU"
        all_items.extend(gpus)
    except Exception as e:
        print(f"  ❌ Ошибка загрузки GPU: {e}")
        print("  ⏭️ Пропуск GPU")

    # CPU из cpu-spec-dataset
    print("\n🔲 CPU (cpubenchmark.net)")
    try:
        raw_cpus = download_csv(CPU_DB_URL)
        cpus = filter_cpus(raw_cpus)
        for cpu in cpus:
            cpu["category"] = "CPU"
        all_items.extend(cpus)
    except Exception as e:
        print(f"  ❌ Ошибка загрузки CPU: {e}")
        print("  ⏭️ Пропуск CPU")

    # RAM, SSD, HDD, M.2 — спецификации производителей
    print("\n💾 RAM/SSD/HDD/M.2")
    all_items = add_manual_data(all_items)

    # Сохранение
    output_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "real_specs.json")

    save_to_json(all_items, output_file)

    print("\n" + "=" * 60)
    print("✅ Загрузка завершена!")
    print("=" * 60)


if __name__ == "__main__":
    main()
