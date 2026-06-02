// file: game.rs --- ゲームの進行や結果表示などを実装するモジュール

use crate::board::{count_stones, stone_name, Board, BLACK, WHITE};
use crate::rules::valid_moves;

// プレイヤーが1手でも打てるかを調べる。
pub fn has_any_move(board: &Board, player: u8) -> bool {
    !valid_moves(board, player).is_empty()
}

// 最終的な石数を表示し、勝者を判定して表示する。
pub fn print_result(board: &Board) {
    let b = count_stones(board, BLACK);
    let w = count_stones(board, WHITE);
    println!("\n結果: 黒={} 白={}", b, w);
    if b > w {
        println!("勝者: {}", stone_name(BLACK));
    } else if w > b {
        println!("勝者: {}", stone_name(WHITE));
    } else {
        println!("引き分けです");
    }
}

// 文字列座標(例: D3)を盤面添字(row, col)へ変換する。
pub fn parse_coord(text: &str) -> Option<(usize, usize)> {
    // 例: "D3" を (row, col) = (2, 3) に変換する。
    let s = text.trim().to_ascii_uppercase();
    if s.len() < 2 || s.len() > 3 {
        return None;
    }

    let mut chars = s.chars();
    let col_ch = chars.next()?;
    if !(('A'..='H').contains(&col_ch)) {
        return None;
    }

    let row_num: usize = chars.as_str().parse().ok()?;
    if !(1..=8).contains(&row_num) {
        return None;
    }

    let col = (col_ch as u8 - b'A') as usize;
    let row = row_num - 1;
    Some((row, col))
}

// 盤面添字(row, col)を文字列座標(例: D3)へ変換する。
pub fn format_coord(row: usize, col: usize) -> String {
    format!("{}{}", (b'A' + col as u8) as char, row + 1)
}

// 相手プレイヤー番号を返す(1<->2)。
pub fn opponent(player: u8) -> u8 {
    if player == 1 { 2 } else { 1 }
}
