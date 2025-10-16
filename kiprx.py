import base64
import hashlib
import json
import os
import platform
import random
import re
import string
import subprocess
import sys
import time
import urllib.parse
import uuid
from datetime import datetime, timedelta, timezone
from time import sleep

# Check và cài đặt các thư viện cần thiết
try:
    from colorama import Fore, Style, init
    init(autoreset=True)
    import pytz
    import requests
except ImportError:
    print('__Đang cài đặt các thư viện cần thiết, vui lòng chờ...__')
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "colorama", "pytz"])
    print('__Cài đặt hoàn tất, vui lòng chạy lại Tool__')
    sys.exit()

# =====================================================================================
# PHẦN 2: MÃ NGUỒN XÁC THỰC (GIỮ NGUYÊN TỪ FILE GỐC)
# =====================================================================================

# CONFIGURATION
FREE_CACHE_FILE = 'free_key_cache.json'
VIP_CACHE_FILE = 'vip_cache.json'
COMPLETED_JOBS_FILE = 'completed_jobs_cache.json' # File mới
HANOI_TZ = pytz.timezone('Asia/Ho_Chi_Minh')
VIP_KEY_URL = "https://raw.githubusercontent.com/DUONGKP2401/KEY-VIP.txt/main/KEY-VIP.txt"

def encrypt_data(data):
    return base64.b64encode(data.encode()).decode()

def decrypt_data(encrypted_data):
    return base64.b64decode(encrypted_data.encode()).decode()

# Colors for display
xnhac = "\033[1;36m"
do = "\033[1;31m"
luc = "\033[1;32m"
vang = "\033[1;33m"
xduong = "\033[1;34m"
hong = "\033[1;35m"
trang = "\033[1;39m"
end = '\033[0m'

def authentication_banner():
    os.system("cls" if os.name == "nt" else "clear")
    banner_text = f"""
████████╗██████╗░██╗░░██╗
╚══██╔══╝██╔══██╗██║░██╔╝
░░░██║░░░██║░░██║█████═╝░
░░░██║░░░██║░░██║██╔═██╗░
░░░██║░░░██████╔╝██║░╚██╗
░░░╚═╝░░░╚═════╝░╚═╝░░╚═╝
══════════════════════════
Admin: DUONG phung
Tool BUMX FB-TDK- hỗ trợ proxy
══════════════════════════
"""
    for char in banner_text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(0.0001)

def get_device_id():
    system = platform.system()
    try:
        if system == "Windows":
            cpu_info = subprocess.check_output('wmic cpu get ProcessorId', shell=True, text=True, stderr=subprocess.DEVNULL)
            cpu_info = ''.join(line.strip() for line in cpu_info.splitlines() if line.strip() and "ProcessorId" not in line)
        else:
            try:
                cpu_info = subprocess.check_output("cat /proc/cpuinfo", shell=True, text=True)
            except:
                cpu_info = platform.processor()
        if not cpu_info:
            cpu_info = platform.processor()
    except Exception:
        cpu_info = "Unknown"

    hash_hex = hashlib.sha256(cpu_info.encode()).hexdigest()
    only_digits = re.sub(r'\D', '', hash_hex)
    if len(only_digits) < 16:
        only_digits = (only_digits * 3)[:16]

    return f"DEVICE-{only_digits[:16]}"

def get_ip_address():
    try:
        response = requests.get('https://api.ipify.org?format=json', timeout=5)
        ip_data = response.json()
        return ip_data.get('ip')
    except Exception:
        return None

def display_machine_info(ip_address, device_id):
    authentication_banner()
    if ip_address:
        print(f"{trang}[{do}<>{trang}] {do}Địa chỉ IP: {vang}{ip_address}{trang}")
    else:
        print(f"{do}Không thể lấy địa chỉ IP của thiết bị.{trang}")

    if device_id:
        print(f"{trang}[{do}<>{trang}] {do}Mã Máy: {vang}{device_id}{trang}")
    else:
        print(f"{do}Không thể lấy Mã Máy của thiết bị.{trang}")

def save_vip_key_info(device_id, key, expiration_date_str):
    data = {'device_id': device_id, 'key': key, 'expiration_date': expiration_date_str}
    encrypted_data = encrypt_data(json.dumps(data))
    with open(VIP_CACHE_FILE, 'w') as file:
        file.write(encrypted_data)

def load_vip_key_info():
    try:
        with open(VIP_CACHE_FILE, 'r') as file:
            encrypted_data = file.read()
        return json.loads(decrypt_data(encrypted_data))
    except (FileNotFoundError, json.JSONDecodeError, TypeError):
        return None

def display_remaining_time(expiry_date_str):
    try:
        expiry_date = datetime.strptime(expiry_date_str, '%d/%m/%Y').replace(hour=23, minute=59, second=59)
        now = datetime.now()

        if expiry_date > now:
            delta = expiry_date - now
            days = delta.days
            hours, remainder = divmod(delta.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            print(f"{xnhac}Key VIP của bạn còn lại: {luc}{days} ngày, {hours} giờ, {minutes} phút.{trang}")
        else:
            print(f"{do}Key VIP của bạn đã hết hạn.{trang}")
    except ValueError:
        print(f"{vang}Không thể xác định ngày hết hạn của key.{trang}")

def check_vip_key(machine_id, user_key):
    print(f"{vang}Đang kiểm tra Key VIP...{trang}")
    try:
        response = requests.get(VIP_KEY_URL, timeout=10)
        if response.status_code != 200:
            return 'error', None

        key_list = response.text.strip().split('\n')
        for line in key_list:
            parts = line.strip().split('|')
            if len(parts) >= 4:
                key_ma_may, key_value, _, key_ngay_het_han = parts

                if key_ma_may == machine_id and key_value == user_key:
                    try:
                        expiry_date = datetime.strptime(key_ngay_het_han, '%d/%m/%Y')
                        if expiry_date.date() >= datetime.now().date():
                            return 'valid', key_ngay_het_han
                        else:
                            return 'expired', None
                    except ValueError:
                        continue
        return 'not_found', None
    except requests.exceptions.RequestException:
        return 'error', None
        
def seeded_shuffle_js_equivalent(array, seed):
    seed_value = 0
    for i, char in enumerate(seed):
        seed_value = (seed_value + ord(char) * (i + 1)) % 1_000_000_000
    def custom_random():
        nonlocal seed_value
        seed_value = (seed_value * 9301 + 49297) % 233280
        return seed_value / 233280.0
    shuffled_array = array[:]
    current_index = len(shuffled_array)
    while current_index != 0:
        random_index = int(custom_random() * current_index)
        current_index -= 1
        shuffled_array[current_index], shuffled_array[random_index] = shuffled_array[random_index], shuffled_array[current_index]
    return shuffled_array

def save_free_key_info(device_id, key, expiration_date):
    data = {device_id: {'key': key, 'expiration_date': expiration_date.isoformat()}}
    encrypted_data = encrypt_data(json.dumps(data))
    with open(FREE_CACHE_FILE, 'w') as file:
        file.write(encrypted_data)

def load_free_key_info():
    try:
        with open(FREE_CACHE_FILE, 'r') as file:
            encrypted_data = file.read()
        return json.loads(decrypt_data(encrypted_data))
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def check_saved_free_key(device_id):
    data = load_free_key_info()
    if data and device_id in data:
        try:
            expiration_date = datetime.fromisoformat(data[device_id]['expiration_date'])
            if expiration_date > datetime.now(HANOI_TZ):
                return data[device_id]['key']
        except (ValueError, KeyError):
            return None
    return None

def generate_free_key_and_url(device_id):
    today_str = datetime.now(HANOI_TZ).strftime('%Y-%m-%d')
    seed_str = f"TDK_FREE_KEY_{device_id}_{today_str}"
    hashed_seed = hashlib.sha256(seed_str.encode()).hexdigest()
    digits = [d for d in hashed_seed if d.isdigit()][:10]
    letters = [l for l in hashed_seed if 'a' <= l <= 'f'][:5]
    while len(digits) < 10:
        digits.extend(random.choices(string.digits))
    while len(letters) < 5:
        letters.extend(random.choices(string.ascii_lowercase))
    key_list = digits + letters
    shuffled_list = seeded_shuffle_js_equivalent(key_list, hashed_seed)
    key = "".join(shuffled_list)
    now_hanoi = datetime.now(HANOI_TZ)
    expiration_date = now_hanoi.replace(hour=21, minute=0, second=0, microsecond=0)
    url = f'https://tdkbumxkey.blogspot.com/2025/10/lay-link.html?m={key}'
    return url, key, expiration_date

def get_shortened_link_phu(url):
    try:
        token = "6725c7b50c661e3428736919"
        api_url = f"https://link4m.co/api-shorten/v2?api={token}&url={urllib.parse.quote(url)}"
        response = requests.get(api_url, timeout=5)
        if response.status_code == 200:
            return response.json()
        return {"status": "error", "message": "Lỗi kết nối dịch vụ rút gọn URL"}
    except Exception:
        return {"status": "error", "message": "Lỗi khi rút gọn URL"}

def process_free_key(device_id):
    if datetime.now(HANOI_TZ).hour >= 21:
        print(f"{do}Đã qua 21:00 giờ Việt Nam, key miễn phí cho hôm nay đã hết hạn.{trang}")
        print(f"{vang}Vui lòng quay lại vào ngày mai để nhận key mới.{trang}")
        time.sleep(3)
        return False

    url, key, expiration_date = generate_free_key_and_url(device_id)
    shortened_data = get_shortened_link_phu(url)

    if shortened_data and shortened_data.get('status') == "error":
        print(f"{do}{shortened_data.get('message')}{trang}")
        return False

    link_key_shortened = shortened_data.get('shortenedUrl')
    if not link_key_shortened:
        print(f"{do}Không thể tạo link rút gọn. Vui lòng thử lại.{trang}")
        return False

    print(f'{trang}[{do}<>{trang}] {hong}Vui Lòng Vượt Link Để Lấy Key Free (Hết hạn 21:00 hàng ngày).{trang}')
    print(f'{trang}[{do}<>{trang}] {hong}Link Để Vượt Key Là {xnhac}: {link_key_shortened}{trang}')

    while True:
        keynhap = input(f'{trang}[{do}<>{trang}] {vang}Key Đã Vượt Là: {luc}')
        if keynhap == key:
            print(f'{luc}Key Đúng! Mời Bạn Dùng Tool{trang}')
            if datetime.now(HANOI_TZ) >= expiration_date:
                print(f"{do}Rất tiếc, key này đã hết hạn vào lúc 21:00. Vui lòng quay lại vào ngày mai.{trang}")
                return False
            time.sleep(2)
            save_free_key_info(device_id, keynhap, expiration_date)
            return True
        else:
            print(f'{trang}[{do}<>{trang}] {hong}Key Sai! Vui Lòng Vượt Lại Link {xnhac}: {link_key_shortened}{trang}')

# ================== CƠ CHẾ LƯU VÀ KIỂM TRA JOB ĐÃ LÀM TRONG NGÀY ==================

def load_completed_jobs_for_today(device_id):
    """
    Tải danh sách các job đã hoàn thành trong ngày hiện tại cho device_id này.
    Nếu là ngày mới (sau 00:00 HNT), danh sách sẽ được reset.
    Trả về set các job_id đã hoàn thành.
    """
    now_hanoi = datetime.now(HANOI_TZ)
    today_str = now_hanoi.strftime('%Y-%m-%d')
    
    data = {}
    try:
        with open(COMPLETED_JOBS_FILE, 'r') as file:
            encrypted_data = file.read()
            data = json.loads(decrypt_data(encrypted_data))
    except (FileNotFoundError, json.JSONDecodeError, TypeError):
        pass

    # Lấy dữ liệu cho device_id và ngày hiện tại
    device_data = data.get(device_id, {})
    
    if device_data.get('date') == today_str:
        return set(device_data.get('completed_jobs', []))
    else:
        # Ngày mới hoặc chưa có dữ liệu, reset
        return set()

def save_completed_job(device_id, job_id):
    """
    Lưu job_id đã hoàn thành vào danh sách của ngày hiện tại.
    """
    now_hanoi = datetime.now(HANOI_TZ)
    today_str = now_hanoi.strftime('%Y-%m-%d')
    
    data = {}
    try:
        with open(COMPLETED_JOBS_FILE, 'r') as file:
            encrypted_data = file.read()
            data = json.loads(decrypt_data(encrypted_data))
    except (FileNotFoundError, json.JSONDecodeError, TypeError):
        # File không tồn tại hoặc lỗi, khởi tạo
        pass

    # Tải dữ liệu hiện tại cho device_id
    device_data = data.get(device_id, {})
    
    # Kiểm tra ngày. Nếu là ngày mới, reset danh sách job
    if device_data.get('date') != today_str:
        device_data = {'date': today_str, 'completed_jobs': []}

    # Thêm job_id nếu chưa có
    if job_id not in device_data['completed_jobs']:
        device_data['completed_jobs'].append(job_id)
        
    data[device_id] = device_data
    
    # Lưu lại
    encrypted_data = encrypt_data(json.dumps(data))
    with open(COMPLETED_JOBS_FILE, 'w') as file:
        file.write(encrypted_data)

# =====================================================================================
# PHẦN 3: TOOL CHÍNH NÂNG CẤP - KẾT NỐI BUMX THẬT
# =====================================================================================

def main_authentication():
    ip_address = get_ip_address()
    device_id = get_device_id()
    display_machine_info(ip_address, device_id)

    if not device_id:
        print(f"{do}Không thể lấy thông tin Mã Máy. Vui lòng kiểm tra lại thiết bị.{trang}")
        return False

    cached_vip_info = load_vip_key_info()
    if cached_vip_info and cached_vip_info.get('device_id') == device_id:
        try:
            expiry_date = datetime.strptime(cached_vip_info['expiration_date'], '%d/%m/%Y')
            if expiry_date.date() >= datetime.now().date():
                print(f"{luc}Đã tìm thấy Key VIP hợp lệ, tự động đăng nhập...{trang}")
                display_remaining_time(cached_vip_info['expiration_date'])
                sleep(3)
                return True
            else:
                print(f"{vang}Key VIP đã lưu đã hết hạn. Vui lòng lấy hoặc nhập key mới.{trang}")
        except (ValueError, KeyError):
            print(f"{do}Lỗi file lưu key VIP. Vui lòng nhập lại key.{trang}")

    if check_saved_free_key(device_id):
        expiry_str = f"21:00 ngày {datetime.now(HANOI_TZ).strftime('%d/%m/%Y')}"
        print(f"{trang}[{do}<>{trang}] {hong}Key free hôm nay vẫn còn hạn (Hết hạn lúc {expiry_str}). Mời bạn dùng tool...{trang}")
        time.sleep(2)
        return True

    while True:
        print(f"{trang}========== {vang}MENU LỰA CHỌN{trang} ==========")
        print(f"{trang}[{luc}1{trang}] {xduong}Nhập Key VIP{trang}")
        print(f"{trang}[{luc}2{trang}] {xduong}Lấy Key Free (Hết hạn 21:00 hàng ngày){trang}")
        print(f"{trang}======================================")

        try:
            choice = input(f"{trang}[{do}<>{trang}] {xduong}Nhập lựa chọn của bạn: {trang}")
            print(f"{trang}═══════════════════════════════════")

            if choice == '1':
                vip_key_input = input(f'{trang}[{do}<>{trang}] {vang}Vui lòng nhập Key VIP: {luc}')
                status, expiry_date_str = check_vip_key(device_id, vip_key_input)

                if status == 'valid':
                    print(f"{luc}Xác thực Key VIP thành công!{trang}")
                    save_vip_key_info(device_id, vip_key_input, expiry_date_str)
                    display_remaining_time(expiry_date_str)
                    sleep(3)
                    return True
                elif status == 'expired':
                    print(f"{do}Key VIP của bạn đã hết hạn. Vui lòng liên hệ admin.{trang}")
                elif status == 'not_found':
                    print(f"{do}Key VIP không hợp lệ hoặc không tồn tại cho mã máy này.{trang}")
                else:
                    print(f"{do}Đã xảy ra lỗi trong quá trình xác thực. Vui lòng thử lại.{trang}")
                sleep(2)

            elif choice == '2':
                return process_free_key(device_id)

            else:
                print(f"{vang}Lựa chọn không hợp lệ, vui lòng nhập 1 hoặc 2.{trang}")

        except KeyboardInterrupt:
            print(f"\n{trang}[{do}<>{trang}] {do}Cảm ơn bạn đã dùng Tool !!!{trang}")
            sys.exit()

# ================== GLOBAL VARIABLES ==================
proxy_list = []
proxy_rotator = None

# ================== PROXY MANAGEMENT NÂNG CẤP ==================
class ProxyRotator:
    def __init__(self, proxies: list):
        self.proxies = proxies[:] if proxies else []
        self.i = 0
        self.dead_proxies = set()

    def has_proxy(self):
        return bool(self.proxies)

    def current(self):
        if not self.proxies:
            return None
        return self.proxies[self.i % len(self.proxies)]

    def rotate(self):
        if not self.proxies:
            return None
        self.i = (self.i + 1) % len(self.proxies)
        return self.current()
    
    def mark_dead(self, proxy):
        if proxy in self.proxies:
            self.dead_proxies.add(proxy)
            # Nếu proxy hiện tại chết, xoay sang proxy tiếp theo
            if self.current() == proxy:
                self.rotate()

def to_requests_proxies(proxy_str):
    if not proxy_str:
        return None
    p = proxy_str.strip().split(':')
    if len(p) == 4:
        try:
            host, port, user, past = p
            int(port)
        except ValueError:
            user, past, host, port = p
        return {
            'http': f'http://{user}:{past}@{host}:{port}',
            'https': f'http://{user}:{past}@{host}:{port}',
        }
    if len(p) == 2:
        host, port = p
        return {
            'http': f'http://{host}:{port}',
            'https': f'http://{host}:{port}',
        }
    return None

def check_proxy_fast(proxy_str):
    """Kiểm tra proxy nhanh với timeout ngắn"""
    try:
        session = requests.Session()
        response = session.get(
            'http://www.google.com/generate_204',
            proxies=to_requests_proxies(proxy_str),
            timeout=5
        )
        return response.status_code in (204, 200)
    except Exception:
        return False

def get_proxy_info(proxy_str):
    """Lấy thông tin IP public của proxy"""
    try:
        session = requests.Session()
        response = session.get(
            'https://api64.ipify.org',
            proxies=to_requests_proxies(proxy_str),
            timeout=8
        )
        if response.status_code == 200:
            return response.text.strip()
    except Exception:
        pass
    return "Unknown"

def add_proxy():
    """Thêm proxy với kiểm tra chất lượng"""
    i = 1
    proxy_list = []
    prints(255, 255, 0, "Nhập Proxy Theo Dạng: username:password:host:port hoặc host:port:username:password")
    prints(255, 255, 0, "Nhấn Enter để bỏ qua và tiếp tục không dùng proxy.")
    
    while True:
        proxy = input(f'Nhập Proxy Số {i}: ').strip()
        if proxy == '':
            if i == 1:
                return []
            break
        
        # Kiểm tra proxy
        prints(255, 255, 0, f'🔍 Đang kiểm tra proxy {i}...')
        if check_proxy_fast(proxy):
            proxy_ip = get_proxy_info(proxy)
            prints(0, 255, 0, f'✅ Proxy Hoạt Động: {proxy} (IP: {proxy_ip})')
            proxy_list.append(proxy)
            i += 1
        else:
            prints(255, 0, 0, f'❌ Proxy Die! Vui lòng nhập proxy khác.')
    
    return proxy_list

def rotate_proxy():
    """Xoay proxy thông minh - chỉ dùng proxy live"""
    global proxy_rotator
    if not proxy_rotator or not proxy_rotator.has_proxy():
        return None
    
    tried = 0
    max_attempts = len(proxy_rotator.proxies)
    
    while tried < max_attempts:
        new_proxy = proxy_rotator.rotate()
        if new_proxy in proxy_rotator.dead_proxies:
            tried += 1
            continue
            
        prints(255, 255, 0, f'🔍 Kiểm tra proxy: {new_proxy}')
        if check_proxy_fast(new_proxy):
            proxy_ip = get_proxy_info(new_proxy)
            prints(0, 255, 0, f'✅ Proxy live: {new_proxy} (IP: {proxy_ip})')
            return new_proxy
        else:
            prints(255, 0, 0, f'❌ Proxy die: {new_proxy}')
            proxy_rotator.mark_dead(new_proxy)
        
        tried += 1
    
    prints(255, 0, 0, '❌ Tất cả proxy đều die!')
    return None

def clear_screen():
    os.system('cls' if platform.system() == "Windows" else 'clear')

def print_enhanced_banner():
    banner_text = """
████████╗██████╗░██╗░░██╗
╚══██╔══╝██╔══██╗██║░██╔╝
░░░██║░░░██║░░██║█████═╝░
░░░██║░░░██║░░██║██╔═██╗░
░░░██║░░░██████╔╝██║░╚██╗
░░░╚═╝░░░╚═════╝░╚═╝░░╚═╝
    """
    
    colors = [
        (255, 0, 0), (255, 127, 0), (255, 255, 0), (0, 255, 0),
        (0, 0, 255), (75, 0, 130), (148, 0, 211), (255, 0, 255)
    ]
    
    color_index = 0
    for line in banner_text.split('\n'):
        for char in line:
            if char not in ' ║╔╗╚╝╠╣╦╩╬═':
                r, g, b = colors[color_index % len(colors)]
                print(f"\033[38;2;{r};{g};{b}m{char}\033[0m", end='')
                color_index += 1
            else:
                print(char, end='')
        print()
    
    print(f"\033[38;2;247;255;97m{'═' * 64}\033[0m")
    
    contacts = [
        ("👥 Zalo Group", "https://zalo.me/g/ddxsyp497"),
        ("✈️ Telegram", "@tankeko12"), 
        ("👑 Admin", "DUONG PHUNG"),
        ("🌐 Proxy", "https://long2k4.id.vn/")
    ]

    for label, info in contacts:
        print(f"\033[38;2;100;200;255m  {label:<15}: \033[0m", end="")
        print(f"\033[38;2;255;255;255m{info}\033[0m")

    print(f"\033[38;2;247;255;97m{'═' * 64}\033[0m")
    print()

def prints(*args, **kwargs):
    r, g, b = 255, 255, 255
    text = ""
    end = "\n"

    if len(args) == 1:
        text = args[0]
    elif len(args) >= 3:
        r, g, b = args[0], args[1], args[2]
        if len(args) >= 4:
            text = args[3]
    if "text" in kwargs:
        text = kwargs["text"]
    if "end" in kwargs:
        end = kwargs["end"]

    print(f"\033[38;2;{r};{g};{b}m{text}\033[0m", end=end)

def encode_to_base64(_data):
    byte_representation = _data.encode('utf-8')
    base64_bytes = base64.b64encode(byte_representation)
    base64_string = base64_bytes.decode('utf-8')
    return base64_string

# ================== FACEBOOK API NÂNG CẤP ==================
def facebook_info_enhanced(cookie: str, proxy: str = None, timeout: int = 20):
    """Phiên bản nâng cấp của facebook_info với retry mechanism"""
    max_retries = 2
    for attempt in range(max_retries):
        try:
            session = requests.Session()
            
            if proxy:
                session.proxies = to_requests_proxies(proxy)
            
            session_id = str(uuid.uuid4())
            user_id = cookie.split("c_user=")[1].split(";")[0] if "c_user=" in cookie else "0"

            headers = {
                "authority": "www.facebook.com",
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                "accept-language": "vi",
                "cookie": cookie,
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36"
            }

            response = session.get(f"https://www.facebook.com/{user_id}", headers=headers, timeout=timeout)
            response_text = response.text

            # Tìm fb_dtsg với nhiều pattern
            fb_dtsg = ""
            patterns = [
                r'\["DTSGInitialData",\[\],\{"token":"(.*?)"\}',
                r'"token":"(.*?)".*?DTSGInitialData',
                r'fb_dtsg.*?"value":"(.*?)"'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, response_text)
                if match:
                    fb_dtsg = match.group(1)
                    break

            jazoest_match = re.search(r'jazoest=(\d+)', response_text)
            jazoest = jazoest_match.group(1) if jazoest_match else ""

            lsd_match = re.search(r'"LSD",\[\],\{"token":"(.*?)"\}', response_text)
            lsd = lsd_match.group(1) if lsd_match else ""

            # Tìm tên với nhiều pattern
            name = "Unknown"
            name_patterns = [
                r'"NAME":"([^"]+)"',
                r'"user":"([^"]+)"',
                r'<title>([^<]+)</title>'
            ]
            
            for pattern in name_patterns:
                match = re.search(pattern, response_text)
                if match:
                    name = match.group(1)
                    break

            if user_id == "0" or not name or name == "Unknown":
                if attempt < max_retries - 1:
                    sleep(2)
                    continue
                return {'success': False}

            return {
                'success': True,
                'user_id': user_id,
                'fb_dtsg': fb_dtsg,
                'jazoest': jazoest,
                'lsd': lsd,
                'name': name,
                'session': session,
                'session_id': session_id,
                'cookie': cookie,
                'headers': headers
            }

        except Exception as e:
            if attempt < max_retries - 1:
                prints(255, 165, 0, f"  ⚠️ Lỗi lấy thông tin FB, thử lại... ({attempt + 1}/{max_retries})")
                sleep(2)
                continue
            else:
                return {'success': False}

def get_post_id_enhanced(session, cookie, link, proxy=None):
    """Lấy post ID với cơ chế retry và fallback"""
    max_retries = 2
    for attempt in range(max_retries):
        try:
            headers = {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'cookie': cookie,
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'
            }
            
            if proxy:
                session.proxies = to_requests_proxies(proxy)
                
            response = session.get(link, headers=headers, timeout=20).text
            response = re.sub(r"\\", "", response)
            
            post_id = ''
            permalink_id = ''
            stories_id = ''
            page_id = ''
            
            # Pattern mạnh mẽ hơn để tìm IDs
            try:
                # Tìm post_id trong JSON
                post_id_matches = re.findall(r'"post_id":"(\d+)"', response)
                if post_id_matches:
                    permalink_id = post_id_matches[0]
            except:
                pass
                
            try:
                # Tìm post ID trong URL
                if '/posts/' in link:
                    post_id = link.split('/posts/')[-1].split('?')[0].split('/')[0]
                elif 'story_fbid=' in response:
                    post_id = re.findall(r'story_fbid=(\d+)', response)[0]
            except:
                pass
                
            try:
                # Tìm stories ID
                if 'stories' in response.lower():
                    stories_matches = re.findall(r'"card_id":"([^"]+)"', response)
                    if stories_matches:
                        stories_id = stories_matches[0]
            except:
                pass
                
            try:
                # Tìm page ID
                page_matches = re.findall(r'"page_id":"(\d+)"', response)
                if page_matches:
                    page_id = page_matches[0]
            except:
                pass
            
            # Nếu không tìm thấy ID nào, thử lại
            if not any([post_id, permalink_id, stories_id, page_id]):
                if attempt < max_retries - 1:
                    sleep(1)
                    continue
            
            return {
                'success': True,
                'post_id': post_id,
                'permalink_id': permalink_id,
                'stories_id': stories_id,
                'page_id': page_id
            }
            
        except Exception as e:
            if attempt < max_retries - 1:
                sleep(1)
                continue
            else:
                return {'success': False}

# ================== BUMX API NÂNG CẤP ==================
def wallet(authorization):
    """Lấy số dư ví với retry mechanism"""
    max_retries = 2
    for attempt in range(max_retries):
        try:
            headers = {
                'User-Agent': 'Dart/3.3 (dart:io)',
                'Content-Type': 'application/json',
                'lang': 'en',
                'version': '37',
                'origin': 'app',
                'authorization': authorization,
            }
            
            response = requests.get('https://api-v2.bumx.vn/api/business/wallet', headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                return data.get('data', {}).get('balance', 'N/A')
            else:
                if attempt < max_retries - 1:
                    sleep(2)
                    continue
                return "Error"
                
        except Exception as e:
            if attempt < max_retries - 1:
                sleep(2)
                continue
            return f"Error"

def get_job_enhanced(session, authorization, proxy=None):
    """Lấy job từ BUMX với retry mechanism"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            headers = {
                'User-Agent': 'Dart/3.3 (dart:io)',
                'lang': 'en',
                'version': '37',
                'origin': 'app',
                'authorization': authorization,
            }
            
            params = {'is_from_mobile': 'true'}
            
            if proxy:
                session.proxies = to_requests_proxies(proxy)
                
            response = session.get('https://api-v2.bumx.vn/api/buff/mission', params=params, headers=headers, timeout=20)
            
            if response.status_code == 200:
                response_json = response.json()
                prints(255, 255, 255, f"✅ Đã tìm thấy {response_json.get('count', 0)} NV")
                
                JOB = []
                for i in response_json.get('data', []):
                    json_job = {
                        "_id": i['_id'],
                        "buff_id": i['buff_id'],
                        "type": i['type'],
                        "name": i['name'],
                        "status": i['status'],
                        "object_id": i['object_id'],
                        "business_id": i['business_id'],
                        "mission_id": i['mission_id'],
                        "create_date": i['create_date'],
                        "note": i['note'],
                        "require": i['require'],
                    }
                    JOB.insert(0, json_job)
                return JOB
            else:
                if attempt < max_retries - 1:
                    prints(255, 165, 0, f"  ⚠️ Lỗi lấy NV, thử lại... ({attempt + 1}/{max_retries})")
                    sleep(3)
                    continue
                    
        except Exception as e:
            if attempt < max_retries - 1:
                prints(255, 165, 0, f"  ⚠️ Lỗi kết nối BUMX, thử lại... ({attempt + 1}/{max_retries})")
                sleep(3)
                continue
    
    prints(255, 0, 0, "  ❌ Không thể lấy NV từ BUMX")
    return []

def load_enhanced(session, authorization, job, proxy=None):
    """Load job với retry mechanism"""
    max_retries = 2
    for attempt in range(max_retries):
        try:
            headers = {
                'User-Agent': 'Dart/3.3 (dart:io)',
                'Content-Type': 'application/json',
                'lang': 'en',
                'version': '37',
                'origin': 'app',
                'authorization': authorization,
            }

            json_data = {'buff_id': job['buff_id']}
            
            if proxy:
                session.proxies = to_requests_proxies(proxy)
                
            response = session.post('https://api-v2.bumx.vn/api/buff/load-mission', headers=headers, json=json_data, timeout=15)
            
            if response.status_code == 200:
                return response.json()
            else:
                if attempt < max_retries - 1:
                    sleep(2)
                    continue
                    
        except Exception as e:
            if attempt < max_retries - 1:
                sleep(2)
                continue
    
    prints(255, 0, 0, "  ❌ Lỗi khi tải thông tin NV")
    return None

def submit_enhanced(session, authorization, job, result_data, res_load, proxy=None):
    """Submit job với retry mechanism"""
    max_retries = 2
    for attempt in range(max_retries):
        try:
            headers = {
                'User-Agent': 'Dart/3.3 (dart:io)',
                'Content-Type': 'application/json',
                'lang': 'en',
                'version': '37',
                'origin': 'app',
                'authorization': authorization,
            }
            
            json_data = {
                'buff_id': job['buff_id'],
                'comment': None, 'comment_id': None, 'code_submit': None,
                'attachments': [], 'link_share': '', 'code': '',
                'is_from_mobile': True, 'type': job['type'], 'sub_id': None, 'data': None,
            }

            if job['type'] == 'like_facebook':
                json_data['comment'] = 'tt nha'
            elif job['type'] == 'like_poster':
                json_data['comment'] = res_load.get('data')
                json_data['comment_id'] = res_load.get('comment_id')
            elif job['type'] == 'review_facebook':
                json_data['comment'] = 'Helo Bạn chúc Bạn sức khỏe '
                json_data['link_share'] = result_data
            
            if proxy:
                session.proxies = to_requests_proxies(proxy)
                
            response = session.post('https://api-v2.bumx.vn/api/buff/submit-mission', headers=headers, json=json_data, timeout=15)
            
            if response.status_code == 200:
                response_data = response.json()
                if response_data.get('success') == True:
                    message = response_data.get('message', '')
                    _xu = '0'
                    sonvdalam = '0'
                    try:
                        _xu = message.split('cộng ')[1].split(',')[0]
                        sonvdalam = message.split('làm: ')[1]
                    except IndexError:
                        pass
                    return [True, _xu, sonvdalam]
            else:
                if attempt < max_retries - 1:
                    sleep(2)
                    continue
                    
        except Exception as e:
            if attempt < max_retries - 1:
                sleep(2)
                continue
    
    return [False, '0', '0']

# ================== JOB EXECUTION NÂNG CẤP ==================
def execute_job_smart(data, job, job_type, current_proxy=None):
    """Thực thi job thông minh với retry mechanism"""
    max_retries = 2
    
    for attempt in range(max_retries):
        try:
            link = 'https://www.facebook.com/' + job['object_id']
            
            if job_type == 'review_facebook':
                # Job review fanpage
                res_get_post_id = get_post_id_enhanced(data['session'], data['cookie'], link, current_proxy)
                if res_get_post_id.get('page_id'):
                    return dexuat_fb_enhanced(data, res_get_post_id['page_id'], job['data'], current_proxy)
                    
            elif job_type == 'like_facebook':
                # Job like với cảm xúc
                react_type = 'LIKE'
                icon = job.get('icon', '').lower()
                if 'love' in icon or 'thuongthuong' in icon: 
                    react_type = 'LOVE'
                elif 'care' in icon: 
                    react_type = 'CARE'
                elif 'wow' in icon: 
                    react_type = 'WOW'
                elif 'sad' in icon: 
                    react_type = 'SAD'
                elif 'angry' in icon: 
                    react_type = 'ANGRY'
                elif 'haha' in icon: 
                    react_type = 'HAHA'
                    
                return react_post_enhanced(data, link, react_type.upper(), current_proxy)
                
            elif job_type == 'like_poster':
                # Job comment
                res_get_post_id = get_post_id_enhanced(data['session'], data['cookie'], link, current_proxy)
                post_id_to_comment = res_get_post_id.get('post_id') or res_get_post_id.get('permalink_id')
                if post_id_to_comment:
                    return comment_fb_enhanced(data, post_id_to_comment, job['data'], current_proxy)
                    
        except Exception as e:
            if attempt < max_retries - 1:
                prints(255, 165, 0, f"  ⚠️ Lỗi thực thi job, thử lại... ({attempt + 1}/{max_retries})")
                sleep(2)
                continue
    
    return False

def react_post_enhanced(data, link, type_react, proxy=None):
    """React post với retry mechanism"""
    max_retries = 2
    for attempt in range(max_retries):
        try:
            res_object_id = get_post_id_enhanced(data['session'], data['cookie'], link, proxy)
            if not res_object_id.get('success'):
                if attempt < max_retries - 1:
                    sleep(1)
                    continue
                return False
                    
            if res_object_id.get('stories_id'):
                return react_stories_enhanced(data, res_object_id['stories_id'], proxy)
            elif res_object_id.get('permalink_id'):
                return react_post_perm_enhanced(data, res_object_id['permalink_id'], type_react, proxy)
            elif res_object_id.get('post_id'):
                return react_post_defaul_enhanced(data, res_object_id['post_id'], type_react, proxy)
                
        except Exception as e:
            if attempt < max_retries - 1:
                sleep(1)
                continue
    
    return False

def react_post_perm_enhanced(data, object_id, type_react, proxy=None):
    """React post perm với retry"""
    max_retries = 2
    for attempt in range(max_retries):
        try:
            prints(255, 255, 0, f'  🎯 Đang thả {type_react}...', end='\r')
            
            react_list = {
                "LIKE": "1635855486666999", "LOVE": "1678524932434102", 
                "CARE": "613557422527858", "HAHA": "115940658764963",
                "WOW": "478547315650144", "SAD": "908563459236466", 
                "ANGRY": "444813342392137"
            }
            
            headers = {
                'accept': '*/*',
                'content-type': 'application/x-www-form-urlencoded',
                'origin': 'https://www.facebook.com',
                'referer': f'https://www.facebook.com/{object_id}',
                'x-fb-lsd': data['lsd'],
                'cookie': data['cookie'],
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'
            }

            json_data = {
                'av': data['user_id'],
                '__user': data['user_id'],
                'fb_dtsg': data['fb_dtsg'],
                'jazoest': data['jazoest'],
                'lsd': data['lsd'],
                'fb_api_caller_class': 'RelayModern',
                'fb_api_req_friendly_name': 'CometUFIFeedbackReactMutation',
                'variables': f'{{"input":{{"attribution_id_v2":"CometSinglePostDialogRoot.react,comet.post.single_dialog,via_cold_start,{int(time.time()*1000)},893597,,,","feedback_id":"{encode_to_base64("feedback:" + object_id)}","feedback_reaction_id":"{react_list.get(type_react.upper())}","feedback_source":"OBJECT","is_tracking_encrypted":true,"tracking":[],"session_id":"{data["session_id"]}","actor_id":"{data["user_id"]}","client_mutation_id":"1"}},"useDefaultActor":false}}',
                'server_timestamps': 'true',
                'doc_id': '24034997962776771',
            }
            
            if proxy:
                data['session'].proxies = to_requests_proxies(proxy)
                
            response = data['session'].post('https://www.facebook.com/api/graphql/', headers=headers, data=json_data, timeout=15)
            if response.status_code == 200:
                prints(0, 255, 0, f'  ✅ Đã thả {type_react} thành công!')
                return True
            else:
                if attempt < max_retries - 1:
                    sleep(1)
                    continue
                    
        except Exception as e:
            if attempt < max_retries - 1:
                sleep(1)
                continue
    
    prints(255, 0, 0, f'  ❌ Thất bại khi thả {type_react}')
    return False

def comment_fb_enhanced(data, object_id, msg, proxy=None):
    """Comment với retry mechanism"""
    max_retries = 2
    for attempt in range(max_retries):
        try:
            prints(255, 255, 0, f'  💬 Đang comment...', end='\r')
            
            headers = {
                'accept': '*/*',
                'content-type': 'application/x-www-form-urlencoded',
                'origin': 'https://www.facebook.com',
                'referer': f'https://www.facebook.com/{object_id}',
                'x-fb-lsd': data['lsd'],
                'cookie': data['cookie'],
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'
            }

            json_data = {
                'av': data['user_id'],
                '__user': data['user_id'],
                'fb_dtsg': data['fb_dtsg'],
                'jazoest': data['jazoest'],
                'lsd': data['lsd'],
                'fb_api_caller_class': 'RelayModern',
                'fb_api_req_friendly_name': 'CometUFICommentCreateMutation',
                'variables': f'{{"input":{{"attachments":[],"feedback_id":"{encode_to_base64("feedback:" + object_id)}","message":{{"ranges":[],"text":"{msg}"}},"tracking":[],"session_id":"{data["session_id"]}","actor_id":"{data["user_id"]}","client_mutation_id":"1"}},"useDefaultActor":false}}',
                'server_timestamps': 'true',
                'doc_id': '5226149245011050',
            }
            
            if proxy:
                data['session'].proxies = to_requests_proxies(proxy)
                
            response = data['session'].post('https://www.facebook.com/api/graphql/', headers=headers, data=json_data, timeout=15)
            if response.status_code == 200:
                prints(0, 255, 0, f'  ✅ Đã comment thành công!')
                return True
            else:
                if attempt < max_retries - 1:
                    sleep(1)
                    continue
                    
        except Exception as e:
            if attempt < max_retries - 1:
                sleep(1)
                continue
    
    prints(255, 0, 0, '  ❌ Thất bại khi comment')
    return False

def dexuat_fb_enhanced(data, object_id, msg, proxy=None):
    """Đề xuất fanpage với retry"""
    max_retries = 2
    for attempt in range(max_retries):
        try:
            prints(255, 255, 0, f'  ⭐ Đang đánh giá fanpage...', end='\r')
            
            if len(msg) <= 25:
                msg += ' ' * (26 - len(msg))

            headers = {
                'accept': '*/*',
                'content-type': 'application/x-www-form-urlencoded',
                'origin': 'https://www.facebook.com',
                'referer': f'https://www.facebook.com/{object_id}',
                'x-fb-lsd': data['lsd'],
                'cookie': data['cookie'],
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'
            }

            json_data = {
                'av': data['user_id'],
                '__user': data['user_id'],
                'fb_dtsg': data['fb_dtsg'],
                'jazoest': data['jazoest'],
                'lsd': data['lsd'],
                'fb_api_caller_class': 'RelayModern',
                'fb_api_req_friendly_name': 'CometPageReviewCreateMutation',
                'variables': f'{{"input":{{"page_id":"{object_id}","rating":5,"recommendation_type":"POSITIVE","review_text":"{msg}","source":"PAGE","tracking":[],"session_id":"{data["session_id"]}","actor_id":"{data["user_id"]}","client_mutation_id":"1"}},"useDefaultActor":false}}',
                'server_timestamps': 'true',
                'doc_id': '6920982595734488',
            }
            
            if proxy:
                data['session'].proxies = to_requests_proxies(proxy)
                
            response = data['session'].post('https://www.facebook.com/api/graphql/', headers=headers, data=json_data, timeout=15)
            if response.status_code == 200:
                prints(0, 255, 0, '  ✅ Đã đánh giá fanpage thành công!')
                return f"https://www.facebook.com/{object_id}"
            else:
                if attempt < max_retries - 1:
                    sleep(1)
                    continue
                    
        except Exception as e:
            if attempt < max_retries - 1:
                sleep(1)
                continue
    
    prints(255, 0, 0, '  ❌ Thất bại khi đánh giá fanpage')
    return False

def react_stories_enhanced(data, object_id, proxy=None):
    """React stories với retry"""
    max_retries = 2
    for attempt in range(max_retries):
        try:
            prints(255, 255, 0, f'  📸 Đang tim story...', end='\r')
            
            headers = {
                'accept': '*/*',
                'content-type': 'application/x-www-form-urlencoded',
                'origin': 'https://www.facebook.com',
                'referer': 'https://www.facebook.com/',
                'x-fb-lsd': data['lsd'],
                'cookie': data['cookie'],
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'
            }

            json_data = {
                'av': data['user_id'],
                '__user': data['user_id'],
                'fb_dtsg': data['fb_dtsg'],
                'jazoest': data['jazoest'],
                'lsd': data['lsd'],
                'fb_api_caller_class': 'RelayModern',
                'fb_api_req_friendly_name': 'useStoriesSendReplyMutation',
                'variables': f'{{"input":{{"attribution_id_v2":"StoriesCometSuspenseRoot.react,comet.stories.viewer,via_cold_start,{int(time.time()*1000)},33592,,,","lightweight_reaction_actions":{{"offsets":[0],"reaction":"❤️"}},"message":"❤️","story_id":"{object_id}","story_reply_type":"LIGHT_WEIGHT","actor_id":"{data["user_id"]}","client_mutation_id":"2"}}}}',
                'server_timestamps': 'true',
                'doc_id': '9697491553691692',
            }
            
            if proxy:
                data['session'].proxies = to_requests_proxies(proxy)
                
            response = data['session'].post('https://www.facebook.com/api/graphql/', headers=headers, data=json_data, timeout=15)
            if response.status_code == 200:
                prints(0, 255, 0, '  ✅ Đã tim story thành công!')
                return True
            else:
                if attempt < max_retries - 1:
                    sleep(1)
                    continue
                    
        except Exception as e:
            if attempt < max_retries - 1:
                sleep(1)
                continue
    
    prints(255, 0, 0, '  ❌ Thất bại khi tim story')
    return False

def react_post_defaul_enhanced(data, object_id, type_react, proxy=None):
    """React post default với retry"""
    return react_post_perm_enhanced(data, object_id, type_react, proxy)

# ================== CÁC HÀM GIỮ NGUYÊN TỪ FILE GỐC ==================
def report(session, authorization, job, retries=3):
    """Báo lỗi job"""
    if retries == 0:
        prints(255, 0, 0, '  💥 Báo lỗi thất bại')
        return

    try:
        headers = {
            'User-Agent': 'Dart/3.3 (dart:io)',
            'Content-Type': 'application/json',
            'lang': 'en',
            'version': '37',
            'origin': 'app',
            'authorization': authorization,
        }
        json_data = {'buff_id': job['buff_id']}
        
        response = session.post('https://api-v2.bumx.vn/api/buff/report-buff', headers=headers, json=json_data, timeout=10)
        prints(255, 165, 0, '  ⚠️ Đã báo lỗi và bỏ qua NV')
    except Exception:
        prints(255, 165, 0, f'  ⚠️ Báo lỗi thất bại, thử lại... ({retries-1})')
        sleep(2)
        report(session, authorization, job, retries - 1)

def reload(session, authorization, type_job, retries=3):
    """Reload job list"""
    if retries == 0:
        return

    try:
        headers = {
            'User-Agent': 'Dart/3.3 (dart:io)',
            'Content-Type': 'application/json',
            'lang': 'en',
            'version': '37',
            'origin': 'app',
            'authorization': authorization,
        }
        json_data = {'type': type_job}
        session.post('https://api-v2.bumx.vn/api/buff/get-new-mission', headers=headers, json=json_data, timeout=10)
    except Exception:
        if retries > 1:
            sleep(2)
            reload(session, authorization, type_job, retries - 1)

def add_account_fb(session, authorization, user_id):
    """Khai báo tài khoản FB với BUMX"""
    try:
        headers = {
            'Content-Type': 'application/json',
            'lang': 'en',
            'version': '37',
            'origin': 'app',
            'authorization': authorization,
        }
        json_data = {'link': f'https://www.facebook.com/profile.php?id={user_id}'}
        response = session.post('https://api-v2.bumx.vn/api/account-facebook/connect-link', headers=headers, json=json_data, timeout=10)
        prints(0, 255, 0, f"  ✅ Đã khai báo tài khoản FB")
    except Exception as e:
        prints(255, 0, 0, f"  ❌ Lỗi khai báo tài khoản FB")

def countdown(seconds):
    """Hiển thị đếm ngược"""
    seconds = int(seconds)
    if seconds < 1: 
        return
    for i in range(seconds, 0, -1):
        prints(147, 112, 219, '[', end='')
        prints(0, 255, 127, "TDK", end='')
        prints(147, 112, 219, ']', end='')
        prints(255, 255, 255, '[', end='')
        prints(255, 215, 0, "WAIT", end='')
        prints(255, 255, 255, ']', end='')
        prints(255, 20, 147, ' ➤ ', end='')
        prints(0, 191, 255, f"⏳ {i}s...", end='\r')
        time.sleep(1)
    print(' ' * 50, end='\r')

def print_state(status_job, _xu, jobdalam, dahoanthanh, tongcanhoanthanh, type_job, name_acc):
    """In trạng thái job"""
    hanoi_tz = timezone(timedelta(hours=7))
    now = datetime.now(hanoi_tz).strftime("%H:%M:%S")
    type_NV = {'like_facebook': '👍 CẢM XÚC', 'like_poster': '💬 COMMENT', 'review_facebook': '⭐ FANPAGE'}
    
    status_color = f"\033[38;2;0;255;0m{status_job.upper()}\033[0m" if status_job.lower() == 'complete' else f"\033[38;2;255;255;0m{status_job.upper()}\033[0m"

    print(f"[{name_acc}]"
          f"[{now}]"
          f"[{dahoanthanh}/{tongcanhoanthanh}]"
          f"[BUMX]"
          f"[{type_NV.get(type_job, 'UNKNOWN')}]"
          f"[{status_color}]"
          f"[+{_xu.strip()}]"
          f"[Đã làm:{jobdalam.strip()}]")

# ================== MAIN TOOL NÂNG CẤP ==================
def main_bumx_free():
    global proxy_list, proxy_rotator
    
    device_id = get_device_id() # Lấy device_id để quản lý job đã làm
    completed_jobs_today = load_completed_jobs_for_today(device_id)

    clear_screen()
    print_enhanced_banner()
    
    # Quản lý proxy
    proxy_list = []
    proxy_rotator = None
    
    if os.path.exists('tdk-proxy-vip.json'):
        prints(66, 245, 245, '🔍 Phát hiện file proxy đã lưu.')
        choice = input(Fore.LIGHTWHITE_EX + 'Bạn có muốn dùng lại proxy đã lưu không? (y/n): ')
        if choice.lower() == 'y':
            try:
                with open('tdk-proxy-vip.json', 'r') as f:
                    proxy_list = json.load(f)
                proxy_rotator = ProxyRotator(proxy_list)
                prints(0, 255, 0, f'✅ Đã tải {len(proxy_list)} proxy từ file')
            except Exception:
                prints(255, 0, 0, '❌ Lỗi đọc file proxy, sẽ nhập mới')
                proxy_list = add_proxy()
                proxy_rotator = ProxyRotator(proxy_list)
                if proxy_list:
                    with open('tdk-proxy-vip.json', 'w') as f:
                        json.dump(proxy_list, f)
        else:
            proxy_list = add_proxy()
            proxy_rotator = ProxyRotator(proxy_list)
            if proxy_list:
                with open('tdk-proxy-vip.json', 'w') as f:
                    json.dump(proxy_list, f)
    else:
        prints(66, 245, 245, '📝 Chưa có file proxy, sẽ nhập mới')
        proxy_list = add_proxy()
        proxy_rotator = ProxyRotator(proxy_list)
        if proxy_list:
            with open('tdk-proxy-vip.json', 'w') as f:
                json.dump(proxy_list, f)
    
    # Quản lý authorization BUMX
    if os.path.exists('tdk-auth-bumx.txt'):
        choice = input(Fore.LIGHTCYAN_EX + 'Bạn có muốn dùng lại authorization BUMX đã lưu không? (y/n): ').lower()
        if choice == 'y':
            with open('tdk-auth-bumx.txt', 'r', encoding='utf-8') as f:
                authorization = f.read().strip()
        else:
            authorization = input(Fore.LIGHTWHITE_EX + 'Nhập authorization BUMX: ').strip()
            with open('tdk-auth-bumx.txt', 'w', encoding='utf-8') as f:
                f.write(authorization)
            prints(0, 255, 0, '✅ Đã lưu authorization')
    else:
        authorization = input(Fore.LIGHTWHITE_EX + 'Nhập authorization BUMX: ').strip()
        with open('tdk-auth-bumx.txt', 'w', encoding='utf-8') as f:
            f.write(authorization)
        prints(0, 255, 0, '✅ Đã lưu authorization')
    
    # Kiểm tra số dư
    balance = wallet(authorization)
    prints(0, 255, 255, f'💰 Số dư: {balance}')
    
    # Tạo session riêng cho BUMX (không dùng proxy)
    bumx_session = requests.Session()

    # Quản lý cookies Facebook
    num_cookies = int(input(Fore.LIGHTCYAN_EX + 'Nhập số lượng cookie Facebook: '))
    cookies_list = []
    valid_cookies = []
    
    for i in range(num_cookies):
        cookie_file = f'tdk-cookie-fb-bumx-{i+1}.txt'
        cookie = ''
        
        if os.path.exists(cookie_file):
            choice = input(Fore.LIGHTCYAN_EX + f'Dùng lại cookie từ {cookie_file}? (y/n): ').lower()
            if choice == 'y':
                with open(cookie_file, 'r', encoding='utf-8') as f:
                    cookie = f.read().strip()
            else:
                cookie = input(Fore.LIGHTCYAN_EX + f'Nhập cookie FB thứ {i+1}: ').strip()
                with open(cookie_file, 'w', encoding='utf-8') as f:
                    f.write(cookie)
                prints(0, 255, 0, f'✅ Đã lưu cookie vào {cookie_file}')
        else:
            cookie = input(Fore.LIGHTCYAN_EX + f'Nhập cookie FB thứ {i+1}: ').strip()
            with open(cookie_file, 'w', encoding='utf-8') as f:
                f.write(cookie)
            prints(0, 255, 0, f'✅ Đã lưu cookie vào {cookie_file}')
        
        if cookie:
            cookies_list.append(cookie)

    if not cookies_list:
        prints(255, 0, 0, "❌ Không có cookie nào được nhập")
        return

    # Kiểm tra cookies hợp lệ
    prints(255, 255, 0, "🔍 Đang kiểm tra cookies...")
    current_proxy = proxy_rotator.current() if proxy_rotator else None
    
    for i, cookie in enumerate(cookies_list):
        account_info = facebook_info_enhanced(cookie, current_proxy)
        if account_info and account_info.get('success'):
            valid_cookies.append(cookie)
            prints(0, 255, 0, f"  ✅ Cookie {i+1}: {account_info['name']}")
        else:
            prints(255, 0, 0, f"  ❌ Cookie {i+1}: Không hợp lệ")

    if not valid_cookies:
        prints(255, 0, 0, "❌ Không có cookie nào hợp lệ")
        return

    # Cấu hình tool
    switch_threshold = int(input(Fore.LIGHTCYAN_EX + 'Sau bao nhiêu NV thì đổi cookie: '))
    
    list_type_job = []
    prints(66, 245, 245, '''
🎯 Các loại nhiệm vụ:
 1. Thả cảm xúc bài viết
 2. Comment vào bài viết  
 3. Đánh giá Fanpage
Nhập STT các loại NV cần làm (ví dụ: 12 để làm cảm xúc và comment): ''', end='')
    
    choice = input()
    job_map = {'1': 'like_facebook', '2': 'like_poster', '3': 'review_facebook'}
    for i in choice:
        job_type = job_map.get(i)
        if job_type:
            list_type_job.append(job_type)
        else:
            prints(255, 0, 0, f'❌ Lựa chọn "{i}" không hợp lệ')
            return

    SO_NV = int(input('Làm bao nhiêu NV thì dừng: '))
    SO_NV1 = SO_NV
    
    delay1 = int(input('Delay tối thiểu (giây): '))
    delay2 = int(input('Delay tối đa (giây): '))

    # Khởi tạo biến
    demht = 0
    demsk = 0
    current_cookie_index = 0
    tasks_on_current_cookie = 0
    
    # Khởi tạo tài khoản đầu tiên
    data = facebook_info_enhanced(valid_cookies[current_cookie_index], current_proxy)
    if not data or not data.get('success'):
        prints(255, 0, 0, "❌ Cookie đầu tiên không hợp lệ")
        return
        
    add_account_fb(bumx_session, authorization, data['user_id'])
    prints(0, 255, 0, f"👤 Đang sử dụng: {data['name']}")

    clear_screen()
    print_enhanced_banner()
    prints(0, 255, 0, f"🚀 Bắt đầu làm {SO_NV} nhiệm vụ...")
    prints(255, 255, 255, "=" * 60)
    prints(147, 112, 219, f"📋 Đã bỏ qua {len(completed_jobs_today)} job đã làm hôm nay.")

    # Vòng lặp chính
    while demht < SO_NV1:
        try:
            # Kiểm tra và xoay proxy nếu cần
            if current_proxy and not check_proxy_fast(current_proxy):
                prints(255, 165, 0, '🔄 Proxy chết, đang tìm proxy mới...')
                current_proxy = rotate_proxy()
                if not current_proxy:
                    prints(255, 0, 0, '⚠️ Tiếp tục không proxy')
                    current_proxy = None

            # Đổi cookie nếu đạt ngưỡng
            if tasks_on_current_cookie >= switch_threshold and len(valid_cookies) > 1:
                current_cookie_index = (current_cookie_index + 1) % len(valid_cookies)
                new_data = facebook_info_enhanced(valid_cookies[current_cookie_index], current_proxy)
                if new_data and new_data.get('success'):
                    data = new_data
                    tasks_on_current_cookie = 0
                    add_account_fb(bumx_session, authorization, data['user_id'])
                    prints(0, 255, 0, f"🔄 Đã chuyển sang: {data['name']}")
                else:
                    prints(255, 0, 0, f"❌ Cookie {current_cookie_index + 1} lỗi, bỏ qua")
                    valid_cookies.pop(current_cookie_index)
                    if not valid_cookies:
                        prints(255, 0, 0, "💥 Tất cả cookie đều lỗi")
                        break
                    current_cookie_index = current_cookie_index % len(valid_cookies)
                    data = facebook_info_enhanced(valid_cookies[current_cookie_index], current_proxy)
                    tasks_on_current_cookie = 0

            # Reload job list
            if not list_type_job:
                prints(0, 255, 0, '✅ Đã hoàn thành tất cả loại job')
                break
            
            for type_job in list_type_job:
                reload(bumx_session, authorization, type_job)
            
            time.sleep(3)
            
            # Lấy job từ BUMX
            JOB = get_job_enhanced(bumx_session, authorization, current_proxy)
            
            if not JOB:
                prints(255, 165, 0, '⏳ Không có job, chờ 10s...', end='\r')
                time.sleep(10)
                continue

            # Xử lý từng job
            for job in JOB:
                if demht >= SO_NV1:
                    break
                    
                # Kiểm tra job đã làm chưa
                if job['buff_id'] in completed_jobs_today:
                    prints(255, 165, 0, f"  🚫 Bỏ qua job {job['buff_id']} ({job['type']}) vì đã làm hôm nay.")
                    demsk += 1
                    continue
                    
                try:
                    # Load job info
                    res_load = load_enhanced(bumx_session, authorization, job, current_proxy)
                    time.sleep(random.randint(2, 3))
                    
                    if res_load and res_load.get('success') and job['type'] in list_type_job:
                        delay = random.randint(delay1, delay2)
                        start_job = time.time()
                        
                        # Thực thi job
                        status_job = execute_job_smart(data, res_load, job['type'], current_proxy)
                        
                        if status_job:
                            # Submit job
                            res_submit = submit_enhanced(bumx_session, authorization, job, status_job, res_load, current_proxy)
                            
                            if res_submit[0]:
                                # Lưu job đã hoàn thành
                                save_completed_job(device_id, job['buff_id'])
                                completed_jobs_today.add(job['buff_id']) 
                                
                                demht += 1
                                tasks_on_current_cookie += 1
                                print_state('complete', res_submit[1], res_submit[2], demht, SO_NV1, job['type'], data['name'])
                                
                                # Delay thông minh
                                elapsed = time.time() - start_job
                                remaining_delay = max(1, delay - elapsed)
                                countdown(remaining_delay)
                            else:
                                raise Exception("Submit thất bại")
                        else:
                            raise Exception("Thực thi job thất bại")
                    else:
                        raise Exception("Job không hợp lệ")

                except Exception as e:
                    prints(255, 165, 0, f"  ⚠️ Lỗi job: {str(e)}")
                    report(bumx_session, authorization, job)
                    demsk += 1
                    time.sleep(3)
        
        except KeyboardInterrupt:
            prints(255, 255, 0, "\n⏹️ Đã dừng bởi người dùng")
            break
        except Exception as e:
            prints(255, 0, 0, f"💥 Lỗi hệ thống: {str(e)}")
            time.sleep(5)

    # Kết thúc
    prints(255, 255, 255, "=" * 60)
    prints(0, 255, 0, f"🎉 HOÀN THÀNH!")
    prints(0, 255, 255, f"✅ Thành công: {demht}")
    prints(255, 165, 0, f"⚠️ Bỏ qua: {demsk}")
    prints(255, 255, 255, f"📊 Tổng: {demsk + demht}")
    prints(255, 255, 255, "=" * 60)
    
    input(f"{Fore.LIGHTWHITE_EX}[{Fore.CYAN}👉{Fore.LIGHTWHITE_EX}] {Fore.YELLOW}Nhấn Enter để tiếp tục...{Fore.RESET}")

# =====================================================================================
# PHẦN 4: CHƯƠNG TRÌNH CHÍNH
# =====================================================================================
if __name__ == "__main__":
    try:
        if main_authentication():
            prints(0, 255, 0, "✅ Xác thực thành công! Bắt đầu tool...")
            time.sleep(2)
            main_bumx_free()
        else:
            prints(255, 0, 0, "❌ Xác thực thất bại!")
            sys.exit()
    except Exception as e:
        prints(255, 0, 0, "💥 Có lỗi xảy ra, vui lòng thử lại!")
        time.sleep(3)
        sys.exit()
