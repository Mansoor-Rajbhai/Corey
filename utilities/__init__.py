# X:\Corey\utilities\__init__.py

from .hardware_monitor import get_complete_specs
from .web_search import search_internet
from .browser_automation import browse_and_interact
from .weather import get_weather
from .system_monitor import get_realtime_usage
from .setting_control import manage_system_settings 

UTILITIES = {
    "get_system_specs": get_complete_specs,
    "internet_search": search_internet,
    "interact_with_site": browse_and_interact,
    "get_weather_data": get_weather,
    "get_realtime_telemetry": get_realtime_usage,
    "control_hardware_settings": manage_system_settings  # 2. Map it here
}