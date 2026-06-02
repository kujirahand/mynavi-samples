// negamax探索でAIの着手を選ぶ
use crate::board::Board;
use crate::game::opponent;
use crate::rules::{apply_move, valid_moves};

const DEPTH: usize = 4; // 探索深さ
const W: [[i32; 8]; 8] = [
    [30, -12, 0, -1, -1, 0, -12, 30],
    [-12, -15, -3, -3, -3, -3, -15, -12],
    [0, -3, 0, -1, -1, 0, -3, 0],
    [-1, -3, -1, -1, -1, -1, -3, -1],
    [-1, -3, -1, -1, -1, -1, -3, -1],
    [0, -3, 0, -1, -1, 0, -3, 0],
    [-12, -15, -3, -3, -3, -3, -15, -12],
    [30, -12, 0, -1, -1, 0, -12, 30],
];

fn evaluate(board: &Board, me: u8) -> i32 {
    let op = opponent(me);
    let mut s = 0;
    for r in 0..8 {
        for c in 0..8 {
            if board[r][c] == me { s += W[r][c]; }
            if board[r][c] == op { s -= W[r][c]; }
        }
    }
    let my_mob = valid_moves(board, me).len() as i32;
    let op_mob = valid_moves(board, op).len() as i32;
    s + (my_mob - op_mob) * 2
}

fn negamax(board: &Board, turn: u8, depth: usize, root: u8) -> i32 {
    let moves = valid_moves(board, turn);
    let op = opponent(turn);
    let op_moves = valid_moves(board, op);
    if depth == 0 || (moves.is_empty() && op_moves.is_empty()) {
        return evaluate(board, root);
    }
    if moves.is_empty() { return -negamax(board, op, depth - 1, root); }
    let mut best = i32::MIN / 2;
    for (r, c) in moves {
        let mut b = *board;
        apply_move(&mut b, r, c, turn);
        best = best.max(-negamax(&b, op, depth - 1, root));
    }
    best
}

pub fn choose_move(board: &Board, ai: u8) -> Option<(usize, usize)> {
    let mut best = None;
    let mut best_score = i32::MIN / 2;
    for (r, c) in valid_moves(board, ai) {
        let mut b = *board;
        apply_move(&mut b, r, c, ai);
        let score = -negamax(&b, opponent(ai), DEPTH - 1, ai);
        if score > best_score { best_score = score; best = Some((r, c)); }
    }
    best
}
