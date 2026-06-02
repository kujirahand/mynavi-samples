// negamax探索でAIの着手を選ぶ
use crate::board::Board;
use crate::game::opponent;
use crate::rules::{apply_move, valid_moves};

const DEPTH: usize = 6; // 探索深さ
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

// 評価関数を複雑にして、盤面の位置、石の数、合法手の数を考慮するようにしたもの
fn evaluate(board: &Board, me: u8) -> i32 {
    let op = opponent(me);

    let mut pos_score = 0;
    let mut my_discs = 0;
    let mut op_discs = 0;
    let mut empty = 0;

    for r in 0..8 {
        for c in 0..8 {
            match board[r][c] {
                x if x == me => {
                    pos_score += W[r][c];
                    my_discs += 1;
                }
                x if x == op => {
                    pos_score -= W[r][c];
                    op_discs += 1;
                }
                _ => {
                    empty += 1;
                }
            }
        }
    }

    let my_mob = valid_moves(board, me).len() as i32;
    let op_mob = valid_moves(board, op).len() as i32;
    let mob_score = my_mob - op_mob;

    let disc_score = my_discs - op_discs;

    if empty >= 40 {
        pos_score * 3 + mob_score * 8
    } else if empty >= 12 {
        pos_score * 2 + mob_score * 6 + disc_score * 2
    } else {
        pos_score + mob_score * 2 + disc_score * 10
    }
}

// 枝刈りの処理を入れたnegamax探索を行う関数
fn negamax(board: &Board, turn: u8, depth: usize, root: u8, mut alpha: i32, beta: i32) -> i32 {
    let mut moves = valid_moves(board, turn);
    let op = opponent(turn);
    let op_moves = valid_moves(board, op);
    if depth == 0 || (moves.is_empty() && op_moves.is_empty()) {
        return evaluate(board, root);
    }
    if moves.is_empty() { return -negamax(board, op, depth - 1, root, -beta, -alpha); }

    // 良さそうな手から探索して枝刈りのヒット率を上げる
    moves.sort_unstable_by(|a, b| W[b.0][b.1].cmp(&W[a.0][a.1]));

    let mut best = i32::MIN / 2;
    for (r, c) in moves {
        let mut b = *board;
        apply_move(&mut b, r, c, turn);
        let score = -negamax(&b, op, depth - 1, root, -beta, -alpha);
        best = best.max(score);
        alpha = alpha.max(score);
        if alpha >= beta {
            break;
        }
    }
    best
}

pub fn choose_move(board: &Board, ai: u8) -> Option<(usize, usize)> {
    let mut moves = valid_moves(board, ai);
    moves.sort_unstable_by(|a, b| W[b.0][b.1].cmp(&W[a.0][a.1]));

    let mut best = None;
    let mut best_score = i32::MIN / 2;
    let mut alpha = i32::MIN / 2;
    let beta = i32::MAX / 2;

    for (r, c) in moves {
        let mut b = *board;
        apply_move(&mut b, r, c, ai);
        let score = -negamax(&b, opponent(ai), DEPTH - 1, ai, -beta, -alpha);
        if score > best_score {
            best_score = score;
            best = Some((r, c));
        }
        alpha = alpha.max(score);
    }
    best
}
