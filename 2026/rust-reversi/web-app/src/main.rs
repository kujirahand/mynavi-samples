// public/ の静的ファイルを配信するシンプルHTTPサーバー
use std::fs;
use std::io::{Read, Write};
use std::net::TcpListener;
use std::path::Path;

fn content_type(path: &str) -> &'static str {
    if path.ends_with(".html") { "text/html; charset=utf-8" }
    else if path.ends_with(".css") { "text/css; charset=utf-8" }
    else if path.ends_with(".js") { "application/javascript; charset=utf-8" }
    else if path.ends_with(".wasm") { "application/wasm" }
    else { "text/plain; charset=utf-8" }
}

fn response(status: &str, ctype: &str, body: &[u8]) -> Vec<u8> {
    let mut out = Vec::new();
    out.extend_from_slice(format!("HTTP/1.1 {}\r\n", status).as_bytes());
    out.extend_from_slice(format!("Content-Type: {}\r\n", ctype).as_bytes());
    out.extend_from_slice(format!("Content-Length: {}\r\n\r\n", body.len()).as_bytes());
    out.extend_from_slice(body);
    out
}

fn main() {
    // 実行ディレクトリに依存しないよう、Cargo.toml基準で public/ を指す。
    let root = format!("{}/public", env!("CARGO_MANIFEST_DIR"));
    let listener = TcpListener::bind("127.0.0.1:7878").expect("bind failed");
    println!("open http://127.0.0.1:7878");

    for mut stream in listener.incoming().flatten() {
        let mut buf = [0_u8; 1024];
        stream.read(&mut buf).ok();
        let req = String::from_utf8_lossy(&buf);
        let mut it = req.lines().next().unwrap_or("").split_whitespace();
        let method = it.next().unwrap_or("");
        let path = it.next().unwrap_or("/");

        let res = if method != "GET" {
            response("405 Method Not Allowed", "text/plain", b"method not allowed")
        } else {
            let url = if path == "/" { "/index.html" } else { path };
            let file = format!("{}{}", root, url);
            if Path::new(&file).is_file() {
                let body = fs::read(&file).unwrap_or_else(|_| b"read error".to_vec());
                response("200 OK", content_type(&file), &body)
            } else {
                response("404 Not Found", "text/plain", b"not found")
            }
        };
        stream.write_all(&res).ok();
    }
}
