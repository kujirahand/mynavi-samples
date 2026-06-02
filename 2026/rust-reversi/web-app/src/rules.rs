// 合法手判定と着手処理
use crate::board::{Board, EMPTY, SIZE};
use crate::game::opponent;

const DIRS: [(isize, isize); 8] = [
    (-1, -1), (-1, 0), (-1, 1), (0, -1),
    (0, 1), (1, -1), (1, 0), (1, 1),
];

fn in_range(r: isize, c: isize) -> bool {
    (0..SIZE as isize).contains(&r) && (0..SIZE as isize).contains(&c)
}

fn flips_dir(b: &Board, row: usize, col: usize, dr: isize, dc: isize, p: u8) -> Vec<(usize, usize)> {
    let mut r = row as isize + dr;
    let mut c = col as isize + dc;
    let mut out = Vec::new();
    while in_range(r, c) {
        let v = b[r as usize][c as usize];
        if v == opponent(p) { out.push((r as usize, c as usize)); }
        else if v == p { return if out.is_empty() { vec![] } else { out }; }
        else { return vec![]; }
        r += dr;
        c += dc;
    }
    vec![]
}

pub fn collect_flips(b: &Board, row: usize, col: usize, p: u8) -> Vec<(usize, usize)> {
    if b[row][col] != EMPTY { return vec![]; }
    let mut out = Vec::new();
    for (dr, dc) in DIRS { out.extend(flips_dir(b, row, col, dr, dc, p)); }
    out
}

pub fn valid_moves(b: &Board, p: u8) -> Vec<(usize, usize)> {
    let mut out = Vec::new();
    for r in 0..SIZE {
        for c in 0..SIZE {
            if !collect_flips(b, r, c, p).is_empty() { out.push((r, c)); }
        }
    }
    out
}

pub fn apply_move(b: &mut Board, row: usize, col: usize, p: u8) -> bool {
    let flips = collect_flips(b, row, col, p);
    if flips.is_empty() { return false; }
    b[row][col] = p;
    for (r, c) in flips { b[r][c] = p; }
    true
}
