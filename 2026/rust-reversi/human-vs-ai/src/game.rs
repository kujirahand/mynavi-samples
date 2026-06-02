// ゲーム進行に共通の補助関数をまとめたモジュール
use crate::board::{count_stones, stone_name, Board, BLACK, WHITE};
use crate::rules::valid_moves;

// 相手プレイヤー番号を返す。
pub fn opponent(player: u8) -> u8 {
    if player == BLACK { WHITE } else { BLACK }
}

// プレイヤーに合法手があるかを判定する。
pub fn has_any_move(board: &Board, player: u8) -> bool {
    !valid_moves(board, player).is_empty()
}

// 終局時の石数と勝者を表示する。
pub fn print_result(board: &Board) {
    let b = count_stones(board, BLACK);
    let w = count_stones(board, WHITE);
    println!("\n結果: 黒={} 白={}", b, w);
    if b > w { println!("勝者: {}", stone_name(BLACK)); }
    else if w > b { println!("勝者: {}", stone_name(WHITE)); }
    else { println!("引き分けです"); }
}