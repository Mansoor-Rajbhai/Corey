# X:\Corey\utilities\system_monitor.py
import psutil
import time
import GPUtil

def get_realtime_usage():
    """
    Samples and returns real-time hardware metrics, including dynamic calculations 
    for network speeds, CPU/RAM utilization, storage, and GPU telemetry.
    """
    try:
        # 1. Sample Network Bytes (Window 1)
        net_start = psutil.net_io_counters()
        time_start = time.time()
        
        # A tiny sleep window to calculate accurate network throughput delta
        time.sleep(0.5)
        
        # 2. Sample Network Bytes (Window 2)
        net_end = psutil.net_io_counters()
        time_end = time.time()
        
        # Calculate speeds (Bytes per second converted to Mbps)
        time_delta = time_end - time_start
        download_speed_mbps = round(((net_end.bytes_recv - net_start.bytes_recv) / time_delta) * 8 / (1024 * 1024), 2)
        upload_speed_mbps = round(((net_end.bytes_sent - net_start.bytes_sent) / time_delta) * 8 / (1024 * 1024), 2)

        # CPU & RAM Usage
        cpu_usage_pct = psutil.cpu_percent(interval=None) # Non-blocking because of the sleep above
        ram = psutil.virtual_memory()
        
        # Storage Diagnostics (Main Drive)
        disk = psutil.disk_usage('C:')
        
        # Temperature Extraction (Core CPU)
        cpu_temps = []
        if hasattr(psutil, "sensors_temperatures"):
            temps = psutil.sensors_temperatures()
            # Try to grab common windows/linux naming schemes
            for key in ['coretemp', 'cpu_thermal', 'amdproctemp', 'acpitz']:
                if key in temps:
                    cpu_temps = [t.current for t in temps[key]]
        avg_cpu_temp = round(sum(cpu_temps) / len(cpu_temps), 1) if cpu_temps else "N/A"

        # GPU Real-time Diagnostics
        gpu_metrics = []
        try:
            gpus = GPUtil.getGPUs()
            for gpu in gpus:
                gpu_metrics.append({
                    "name": gpu.name,
                    "load_pct": f"{round(gpu.load * 100, 1)}%",
                    "vram_used_mb": round(gpu.memoryUsed, 1),
                    "vram_total_mb": round(gpu.memoryTotal, 1),
                    "vram_usage_pct": f"{round(gpu.memoryUtil * 100, 1)}%",
                    "temperature_celsius": f"{gpu.temperature}°C"
                })
        except Exception:
            # Fallback if no dedicated GPU or drivers are missing
            gpu_metrics = "No dedicated GPU detected or GPUtil driver error."

        return {
            "status": "success",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "cpu": {
                "usage_percentage": f"{cpu_usage_pct}%",
                "average_temperature": f"{avg_cpu_temp}°C" if avg_cpu_temp != "N/A" else "N/A"
            },
            "ram": {
                "used_gb": round(ram.used / (1024**3), 2),
                "total_gb": round(ram.total / (1024**3), 2),
                "usage_percentage": f"{ram.percent}%"
            },
            "storage_c_drive": {
                "used_gb": round(disk.used / (1024**3), 2),
                "total_gb": round(disk.total / (1024**3), 2),
                "usage_percentage": f"{disk.percent}%"
            },
            "network_throughput": {
                "download_speed": f"{download_speed_mbps} Mbps",
                "upload_speed": f"{upload_speed_mbps} Mbps"
            },
            "gpu": gpu_metrics
        }
        
    except Exception as e:
        return {"status": "error", "message": f"Telemetry capture failure: {str(e)}"}