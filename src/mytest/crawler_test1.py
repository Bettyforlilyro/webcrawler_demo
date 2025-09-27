import requests
from bs4 import BeautifulSoup

# 目标网址（示例使用 httpbin 提供的测试页面）
url = 'http://www.ujxsw.org/book/1022/'

# 发送 HTTP 请求
try:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.1000.0 Safari/537.36'
    }
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()  # 如果状态码不是200，抛出异常
except requests.exceptions.RequestException as e:
    print(f"请求失败: {e}")
    exit()

# 解析 HTML
soup = BeautifulSoup(response.text, 'html.parser')

# 获取标题
title = soup.title.string if soup.title else "无标题"
print(f"页面标题: {title}\n")

# 获取所有链接
links = soup.find_all('a')
if not links:
    print("未找到任何链接。")
else:
    print("页面中的链接：")
    for i, link in enumerate(links, 1):
        text = link.get_text(strip=True) or "无文字"
        href = link.get('href') or "无链接"
        print(f"{i}. 文字: {text} → 链接: {href}")