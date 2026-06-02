mod board;
mod game;
mod rules;

use std::io;

use board::{new_board, print_board, stone_name, BLACK};
use game::{format_coord, has_any_move, opponent, parse_coord, print_result};
use rules::{apply_move, valid_moves};

// 標準入力から1行読み取り、前後の空白を除いて返す。
fn read_line() -> String {
    let mut s = String::new();
    io::stdin().read_line(&mut s).ok();
    s.trim().to_string()
}

// 人間同士で対戦するメインループを実行する。
fn main() {
    let mut board = new_board();
    let mut current = BLACK;

    loop {
        print_board(&board);
        if !has_any_move(&board, current) && !has_any_move(&board, opponent(current)) { break; }
        if !has_any_move(&board, current) {
            println!("{} は置ける場所がないのでパス", stone_name(current));
            current = opponent(current);
            continue;
        }

        let moves = valid_moves(&board, current);
        let labels: Vec<String> = moves.iter().map(|&(r, c)| format_coord(r, c)).collect();
        println!("\n{} の手番。置ける場所: {}", stone_name(current), labels.join(", "));
        println!("座標を入力 (例: D3, 終了: q)");
        let input = read_line();
        if input.eq_ignore_ascii_case("q") { break; }

        if let Some((row, col)) = parse_coord(&input) {
            if apply_move(&mut board, row, col, current) { current = opponent(current); }
            else { println!("その場所には置けません。\n"); }
        } else {
            println!("入力形式が不正です。例: A1, H8\n");
        }
    }

    print_board(&board);
    print_result(&board);
}
