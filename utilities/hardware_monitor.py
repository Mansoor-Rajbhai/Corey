# X:\Corey\utilities\hardware_monitor.py
import subprocess
import psutil

def _run_ps_cmd(property_name: str, cim_class: str) -> str:
    """Helper to query modern Windows CIM instances via PowerShell."""
    try:
        cmd = f"powershell -Command \"(Get-CimInstance -ClassName {cim_class}).{property_name}\""
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL)
        result = output.decode("utf-8").strip()
        return result if result else "Unknown"
    except Exception:
        return "Unknown"

def _get_cpu_temp() -> str:
    """Alternative method to pull real-time thermal zone telemetry on modern laptops."""
    try:
        # Fallback 1: Performance Counters (more reliable on modern Win11 Dell builds)
        cmd = "powershell -Command \"(Get-CimInstance -ClassName Win32_PerfFormattedData_Counters_ThermalZoneInformation).Temperature\""
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode("utf-8").strip()
        
        if not output or "Unknown" in output:
            # Fallback 2: ACPI baseline
            cmd = "powershell -Command \"(Get-CimInstance -Namespace root/wmi -ClassName MSAcpi_ThermalZoneTemperature).CurrentTemperature\""
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode("utf-8").strip()
            if output:
                raw_temp = float(output.split()[0])
                celsius = (raw_temp / 10.0) - 273.15
                return f"{round(celsius, 1)}°C"
        else:
            # Performance counter returns Kelvin directly or absolute relative offset
            raw_temp = float(output.split()[0])
            if raw_temp > 200: 
                return f"{round(raw_temp - 273.15, 1)}°C"
            return f"{raw_temp}°C"
            
        return "N/A (Hardware Restricted)"
    except Exception:
        return "N/A"

def get_complete_specs():
    """Gathers true A to Z system specs including total physical disk sizes and refined temperatures."""
    
    # 1. Device Core Identity
    system_vendor = _run_ps_cmd("Manufacturer", "Win32_ComputerSystem")
    system_model = _run_ps_cmd("Model", "Win32_ComputerSystem")
    system_version = _run_ps_cmd("Version", "Win32_ComputerSystemProduct") 

    # 2. Base Motherboard Details
    mb_product = _run_ps_cmd("Product", "Win32_BaseBoard")
    mb_serial = _run_ps_cmd("SerialNumber", "Win32_BaseBoard")

    # 3. Processing Chip
    cpu_brand = _run_ps_cmd("Name", "Win32_Processor")
    
    # 4. Display Arrays
    gpu_raw = _run_ps_cmd("Name", "Win32_VideoController")
    gpu_list = [g.strip() for g in gpu_raw.replace("\r", "").split("\n") if g.strip()]

    # 5. OS Profile
    os_name = _run_ps_cmd("Caption", "Win32_OperatingSystem")
    os_build = _run_ps_cmd("BuildNumber", "Win32_OperatingSystem")
    os_architecture = _run_ps_cmd("OSArchitecture", "Win32_OperatingSystem")
    
    # 6. Physical Drive Models & Total Physical Capacity Calculation
    drive_models_raw = _run_ps_cmd("Model", "Win32_DiskDrive")
    drive_brands = [d.strip() for d in drive_models_raw.replace("\r", "").split("\n") if d.strip()]
    
    drive_sizes_raw = _run_ps_cmd("Size", "Win32_DiskDrive")
    total_physical_gb = 0
    try:
        for size in drive_sizes_raw.split("\n"):
            if size.strip().isdigit():
                total_physical_gb += int(size.strip()) / (1024 ** 3)
    except Exception:
        pass

    # 7. Dynamic Partition Metrics (C:\, X:\, etc.)
    partitions = {}
    for part in psutil.disk_partitions():
        if 'fixed' in part.opts or part.fstype:
            try:
                usage = psutil.disk_usage(part.mountpoint)
                partitions[part.mountpoint] = {
                    "total_gb": round(usage.total / (1024 ** 3), 1),
                    "used_gb": round(usage.used / (1024 ** 3), 1),
                    "free_gb": round(usage.free / (1024 ** 3), 1),
                    "percent_used": usage.percent
                }
            except PermissionError:
                continue

    # 8. Dynamic Memory Real-time Loads
    memory = psutil.virtual_memory()
    
    return {
        "hardware_specs": {
            "device_identity": {
                "brand": system_vendor,
                "model_number": system_model,
                "model_version": system_version
            },
            "motherboard": {
                "board_model": mb_product,
                "serial_number": mb_serial
            },
            "processor": {
                "full_brand_name": cpu_brand,
                "physical_cores": psutil.cpu_count(logical=False),
                "logical_threads": psutil.cpu_count(logical=True),
                "architecture": os_architecture
            },
            "graphics_card": {
                "gpu_models": gpu_list
            },
            "storage_hardware": {
                "physical_drives": drive_brands,
                "total_hardware_capacity_gb": round(total_physical_gb, 1)
            },
            "operating_system": f"{os_name} (Build {os_build})"
        },
        "live_telemetry": {
            "core_temperature": _get_cpu_temp(),
            "cpu_utilization_percent": psutil.cpu_percent(interval=None),
            "ram_utilization_percent": memory.percent,
            "ram_used_gb": round(memory.used / (1024 ** 3), 2),
            "ram_total_gb": round(memory.total / (1024 ** 3), 2),
            "logical_storage_volumes": partitions
        }
    }