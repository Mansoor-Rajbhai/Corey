# File: X:\Corey\services\RAS\start_ras.py
import time
import requests
from pycloudflared import try_cloudflare

LOCAL_PORT = 5000

def shorten_link(long_url):
    """Uses the free Is.gd API to shorten the Cloudflare tunnel link securely."""
    try:
        # Using a dictionary for params automatically handles URL-encoding characters like : and /
        api_url = "https://is.gd"
        payload = {'format': 'simple', 'url': long_url}
        
        response = requests.get(api_url, params=payload, timeout=5)
        
        if response.status_code == 200:
            return response.text.strip()
        else:
            print(f"[!] Shortener API returned status code: {response.status_code}")
    except Exception as e:
        print(f"[!] Shortener failed: {e}")
        
    return long_url  # Fallback only if the request completely fails

def main():
    print("\n" + "═"*50)
    print("🛰️  COREY REMOTE ACCESSIBLE SERVER (RAS)")
    print("═"*50)
    print(f"[*] Locating continuous local server on port {LOCAL_PORT}...")
    
    try:
        # 1. Establish the global tunnel 
        print("[*] Initiating secure connection bridge...")
        public_url_obj = try_cloudflare(port=LOCAL_PORT)
        
        # 2. Extract the actual tunnel URL string
        tunnel_url = public_url_obj.tunnel
        
        # 3. Compress the clean string URL
        print("[*] Generating easy-access short link...")
        short_url = shorten_link(tunnel_url)
        
        print("\n" + "═"*50)
        print("🚀 COREY PORTAL IS NOW GLOBAL!")
        print(f"🔗 Long Address: {tunnel_url}")
        print(f"👉 Portal URL:  {short_url}")
        print("═"*50)
        print("\n[!] Keeping this bridge active.")
        print("[!] Close this window or press Ctrl+C to terminate global access.")
        
        # Keep the tunnel running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n[-] Global access terminated safely. Local server remains online.")
    except Exception as e:
        print(f"\n[!] Failed to establish global tunnel: {e}")

if __name__ == "__main__":
    main()
