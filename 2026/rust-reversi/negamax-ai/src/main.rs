mod ai;
mod board;
mod coord;
mod game;
mod rules;

use std::io;

use ai::choose_move;
use board::{new_board, print_board, stone_name, BLACK, WHITE};
use coord::{format_coord, parse_coord};
use game::{has_any_move, opponent, print_result};
use rules::{apply_move, valid_moves};

// 標準入力から1行だけ読み込む。
fn read_line() -> String {
    let mut s = String::new();
    io::stdin().read_line(&mut s).ok();
    s.trim().to_string()
}

// 人間(黒) vs negamax AI(白)の対戦を実行する。
fn main() {
    let mut board = new_board();
    let mut current = BLACK;

    loop {
        println!("-------------------------");
        print_board(&board);
        if !has_any_move(&board, current) && !has_any_move(&board, opponent(current)) { break; }
        if !has_any_move(&board, current) {
            println!("{} は置ける場所がないのでパス", stone_name(current));
            current = opponent(current);
            continue;
        }

        if current == BLACK {
            let moves = valid_moves(&board, BLACK);
            let labels: Vec<String> = moves.iter().map(|&(r, c)| format_coord(r, c)).collect();
            println!("\n>>> あなた(黒)の手番: 置ける場所: {}", labels.join(", "));
            let input = read_line();
            if input.eq_ignore_ascii_case("q") { break; }
            if let Some((r, c)) = parse_coord(&input) {
                if !apply_move(&mut board, r, c, BLACK) { println!("その場所には置けません。\n"); continue; }
            } else {
                println!("入力形式が不正です。例: A1, H8\n");
                continue;
            }
        } else if let Some((r, c)) = choose_move(&board, WHITE) {
            println!("\nnegamax AI(白)は {} に置きました", format_coord(r, c));
            apply_move(&mut board, r, c, WHITE);
        }
        current = opponent(current);
    }

    println!("-------------------------");
    print_board(&board);
    print_result(&board);
}
