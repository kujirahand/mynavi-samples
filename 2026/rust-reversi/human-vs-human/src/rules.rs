// file: rule.rs --- リバーシのルールを実装するモジュール
use crate::board::{Board, EMPTY, SIZE};
use crate::game::opponent;

const DIRS: [(isize, isize); 8] = [ // 8方向を表す --- (*1)
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
];

// 盤面の範囲内かどうかを判定する --- (*2)
fn in_range(r: isize, c: isize) -> bool {
    (0..SIZE as isize).contains(&r) && (0..SIZE as isize).contains(&c)
}

// 1方向だけ調べて、反転できる相手石の座標を集める --- (*3)
fn flips_in_dir(board: &Board, row: usize, col: usize, dr: isize, dc: isize, p: u8) -> Vec<(usize, usize)> {
    // 相手石をたどり、最後に自分の石で挟めたら反転対象として返す。
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

// 8方向を調べて、着手時に反転される石をすべて返す --- (*4)
pub fn collect_flips(board: &Board, row: usize, col: usize, p: u8) -> Vec<(usize, usize)> {
    if board[row][col] != EMPTY { return vec![]; }
    let mut flips = Vec::new();
    for (dr, dc) in DIRS {
        flips.extend(flips_in_dir(board, row, col, dr, dc, p));
    }
    flips
}

// 現在のプレイヤーが置ける全座標を返す --- (*5)
pub fn valid_moves(board: &Board, p: u8) -> Vec<(usize, usize)> {
    let mut moves = Vec::new();
    for r in 0..SIZE {
        for c in 0..SIZE {
            if !collect_flips(board, r, c, p).is_empty() { moves.push((r, c)); }
        }
    }
    moves
}

// 指定座標に着手し、反転を適用する。置けない場合はfalseを返す --- (*6)
pub fn apply_move(board: &mut Board, row: usize, col: usize, p: u8) -> bool {
    let flips = collect_flips(board, row, col, p);
    if flips.is_empty() { return false; }
    board[row][col] = p;
    for (r, c) in flips { board[r][c] = p; }
    true
}