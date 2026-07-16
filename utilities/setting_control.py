# X:\Corey\utilities\settings_control.py
import subprocess
from pycaw.pycaw import AudioUtilities
import screen_brightness_control as sbc

def manage_system_settings(action: str, target: str, value=None):
    """
    Corey's Elevated Hardware Manager. Requires an Administrator terminal to
    programmatically alter network adapters, driver states, and device registries.
    """
    try:
        action = action.lower().strip()
        target = target.lower().strip()

        # 1. BRIGHTNESS MANAGEMENT
        if target == "brightness":
            if action == "set" and value is not None:
                sbc.set_brightness(int(value))
                return {"status": "success", "message": f"Screen brightness set to {value}%"}
            elif action == "get":
                return {"status": "success", "brightness": f"{sbc.get_brightness()[0]}%"}

        # 2. AUDIO VOLUME & MUTE MANAGEMENT (Patched explicitly for exact Win32 Boolean mapping)
        elif target == "volume":
            device = AudioUtilities.GetSpeakers()
            volume_endpoint = device.EndpointVolume
            
            if action == "set" and value is not None:
                volume_endpoint.SetMasterVolumeLevelScalar(int(value) / 100.0, None)
                return {"status": "success", "message": f"System volume level adjusted to {value}%"}
            elif action == "get":
                current_v = volume_endpoint.GetMasterVolumeLevelScalar()
                is_muted = volume_endpoint.GetMute()
                return {"status": "success", "volume": f"{round(current_v * 100)}%", "is_muted": bool(is_muted)}
            elif action == "mute":
                # Forces explicit True boolean across the COM register
                volume_endpoint.SetMute(True, None)
                return {"status": "success", "message": "Audio muted successfully"}
            elif action == "unmute":
                # Forces explicit False boolean across the COM register
                volume_endpoint.SetMute(False, None)
                return {"status": "success", "message": "Audio unmuted successfully"}

        # 3. WI-FI TOGGLE (Elevated PowerShell NetAdapter Pipeline)
        elif target == "wifi":
            ps_state = "Enable-NetAdapter" if action in ["on", "enable"] else "Disable-NetAdapter"
            cmd = f'powershell -ExecutionPolicy Bypass -Command "{ps_state} -Name \'Wi-Fi\' -Confirm:$false"'
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if res.returncode != 0:
                return {"status": "error", "message": f"Wi-Fi execution blocked: {res.stderr.strip()}"}
            return {"status": "success", "message": f"Wi-Fi hardware adapter successfully turned {action.upper()}"}

        # 4. BLUETOOTH TOGGLE (Elevated PnpDevice Driver Stack)
        elif target == "bluetooth":
            ps_state = "Enable-PnpDevice" if action in ["on", "enable"] else "Disable-PnpDevice"
            cmd = f'powershell -ExecutionPolicy Bypass -Command "Get-PnpDevice -Class Bluetooth | {ps_state} -Confirm:$false"'
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if res.returncode != 0:
                return {"status": "error", "message": f"Bluetooth driver flip blocked: {res.stderr.strip()}"}
            return {"status": "success", "message": f"Bluetooth hardware state successfully forced {action.upper()}"}

        # 5. LOCATION / GPS TOGGLE (Elevated Registry Overrides)
        elif target in ["location", "gps"]:
            reg_val = "0" if action in ["on", "enable"] else "1"
            cmd = f'powershell -ExecutionPolicy Bypass -Command "Set-ItemProperty -Path \'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\LocationAndSensors\' -Name \'DisableLocation\' -Value {reg_val} -Force"'
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            app_val = "1" if action in ["on", "enable"] else "2"
            cmd_app = f'powershell -ExecutionPolicy Bypass -Command "Set-ItemProperty -Path \'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\AppPrivacy\' -Name \'LetAppsAccessLocation\' -Value {app_val} -Force"'
            subprocess.run(cmd_app, shell=True, capture_output=True)
            
            if res.returncode != 0:
                return {"status": "error", "message": f"Registry write blocked: {res.stderr.strip()}"}
            return {"status": "success", "message": f"Location Services privacy registry key successfully forced {action.upper()}"}

        return {"status": "error", "message": "Invalid settings parameter combination."}

    except Exception as e:
        return {"status": "error", "message": f"Settings driver engine failure: {str(e)}"}