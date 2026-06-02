// WebAssemblyとして公開する入口
use wasm_bindgen::prelude::*;

mod ai;
mod board;
mod game;
mod rules;

use board::{Board, SIZE};

// JavaScriptの一次元配列をRustの8x8盤面に変換する。
fn to_board(data: &[u8]) -> Board {
    let mut b = [[0_u8; SIZE]; SIZE];
    for r in 0..SIZE {
        for c in 0..SIZE {
            b[r][c] = data[r * SIZE + c];
        }
    }
    b
}

// AIの手を返す。戻り値は row * 8 + col、打てない時は -1。
#[wasm_bindgen]
pub fn choose_move(data: &[u8], ai_player: u8) -> i32 {
    let board = to_board(data);
    match ai::choose_move(&board, ai_player) {
        Some((r, c)) => (r * SIZE + c) as i32,
        None => -1,
    }
}
