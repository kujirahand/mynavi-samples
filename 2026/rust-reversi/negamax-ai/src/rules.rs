// リバーシの合法手判定と着手処理を担当するモジュール
use crate::board::{Board, EMPTY, SIZE};
use crate::game::opponent;

const DIRS: [(isize, isize); 8] = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
];

// 指定座標が盤面の内側かを判定する。
fn in_range(r: isize, c: isize) -> bool {
    (0..SIZE as isize).contains(&r) && (0..SIZE as isize).contains(&c)
}

// 1方向だけ見て反転対象の石を集める。
fn flips_in_dir(board: &Board, row: usize, col: usize, dr: isize, dc: isize, p: u8) -> Vec<(usize, usize)> {
    let mut r = row as isize + dr;
    let mut c = col as isize + dc;
    let mut tmp = Vec::new();
    while in_range(r, c) {
        let v = board[r as usize][c as usize];
        if v == opponent(p) { tmp.push((r as usize, c as usize)); }
        else if v == p { return if tmp.is_empty() { vec![] } else { tmp }; }
        else { return vec![]; }
        r += dr;
        c += dc;
    }
    vec![]
}

// 8方向の反転対象をすべて返す。
pub fn collect_flips(board: &Board, row: usize, col: usize, p: u8) -> Vec<(usize, usize)> {
    if board[row][col] != EMPTY { return vec![]; }
    let mut flips = Vec::new();
    for (dr, dc) in DIRS { flips.extend(flips_in_dir(board, row, col, dr, dc, p)); }
    flips
}

// プレイヤーの合法手一覧を返す。
pub fn valid_moves(board: &Board, p: u8) -> Vec<(usize, usize)> {
    let mut moves = Vec::new();
    for r in 0..SIZE {
        for c in 0..SIZE {
            if !collect_flips(board, r, c, p).is_empty() { moves.push((r, c)); }
        }
    }
    moves
}

// 着手を適用して石を反転する。失敗時はfalse。
pub fn apply_move(board: &mut Board, row: usize, col: usize, p: u8) -> bool {
    let flips = collect_flips(board, row, col, p);
    if flips.is_empty() { return false; }
    board[row][col] = p;
    for (r, c) in flips { board[r][c] = p; }
    true
}