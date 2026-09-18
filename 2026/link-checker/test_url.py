from urllib.parse import urljoin, urldefrag

base_url = "https://example.com/docs/page.html"

# 相対URLを絶対URLに変換
url = urljoin(base_url, "../index.html#section1")
print(url) # https://example.com/index.html#section1 

# `#`以降のフラグメントを取り除く
url, fragment = urldefrag(url)
print(url) # https://example.com/index.html
print(fragment) # section1


