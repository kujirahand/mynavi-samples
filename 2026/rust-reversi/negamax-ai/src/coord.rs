// 座標文字列と配列添字の相互変換モジュール

// "D3" のような座標を (row, col) に変換する。
pub fn parse_coord(text: &str) -> Option<(usize, usize)> {
    let s = text.trim().to_ascii_uppercase();
    if s.len() < 2 || s.len() > 3 { return None; }

    let mut chars = s.chars();
    let col_ch = chars.next()?;
    if !(('A'..='H').contains(&col_ch)) { return None; }

    let row_num: usize = chars.as_str().parse().ok()?;
    if !(1..=8).contains(&row_num) { return None; }

    Some((row_num - 1, (col_ch as u8 - b'A') as usize))
}

// (row, col) を "D3" のような座標へ変換する。
pub fn format_coord(row: usize, col: usize) -> String {
    format!("{}{}", (b'A' + col as u8) as char, row + 1)
}