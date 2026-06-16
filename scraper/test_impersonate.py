from curl_cffi import requests

proxy = "http://tkkmtayv:8hb0qw0a0gy0@38.154.203.95:5863"
proxies = {"http": proxy, "https": proxy}
url = "https://www.wasi.lk/product-category/computers-laptops/laptops/"

profiles = ["chrome100", "chrome110", "chrome116", "chrome120", "safari15_3", "safari15_5", "edge101"]

for p in profiles:
    try:
        r = requests.get(url, proxies=proxies, impersonate=p, timeout=10)
        print(f"{p}: {r.status_code}")
    except Exception as e:
        print(f"{p}: ERROR - {e}")
