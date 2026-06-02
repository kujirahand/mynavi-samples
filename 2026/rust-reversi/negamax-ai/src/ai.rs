// file: ai.rs --- negamax探索でAIの着手を選ぶモジュール
use crate::board::Board;
use crate::rules::{apply_move, valid_moves};
use crate::game::opponent;

// 探索深さ。大きいほど強いが遅くなる --- (*1)
const DEPTH: usize = 4;

// 盤面の位置ごとの重みを指定 --- (*2)
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

// 静的評価値(位置 + 合法手数差)を返す --- (*3)
fn evaluate(board: &Board, me: u8) -> i32 {
    let opp = opponent(me);
    let mut s = 0;
    for r in 0..8 {
        for c in 0..8 {
            if board[r][c] == me { s += W[r][c]; }
            if board[r][c] == opp { s -= W[r][c]; }
        }
    }
    let my_mob = valid_moves(board, me).len() as i32;
    let op_mob = valid_moves(board, opp).len() as i32;
    s + (my_mob - op_mob) * 2
}

// negamaxで現在手番の最善評価を返す --- (*4)
fn negamax(board: &Board, turn: u8, depth: usize, root: u8) -> i32 {
    // 現手番と相手の合法手を先に作って、終端判定やパス判定に使う --- (*5)
    let my_moves = valid_moves(board, turn); // 自分の合法手
    let op = opponent(turn); // 
    let op_moves = valid_moves(board, op);

    // これ以上読まない深さ、または両者とも打てない終局なら静的評価を返す --- (*6)
    if depth == 0 || (my_moves.is_empty() && op_moves.is_empty()) {
        return evaluate(board, root);
    }

    // 自分だけ打てないときはパスして、手番を交代して評価の符号を反転する --- (*7)
    // negamaxでは「相手の最善 = 自分から見た最悪」なので -1 を掛ける
    if my_moves.is_empty() { return -negamax(board, op, depth - 1, root); }

    // 全合法手を試して、最も評価値が高いものを採用する --- (*8)
    let mut best = i32::MIN / 2;
    for (r, c) in my_moves {
        // 盤面をコピーして再帰的に評価を得る(視点交代のため評価反転) --- (*9)
        let mut b = *board;
        apply_move(&mut b, r, c, turn);
        let score = -negamax(&b, op, depth - 1, root);

        // 現手番から見て最大の評価値を採用 --- (*10)
        if score > best { best = score; }
    }
    best
}

// 全合法手を探索し、最も評価が高い手を返す --- (*11)
pub fn choose_move(board: &Board, ai: u8) -> Option<(usize, usize)> {
    let mut best = None;
    let mut best_score = i32::MIN / 2;
    let op = opponent(ai);
    for (r, c) in valid_moves(board, ai) {
        let mut b = *board;
        apply_move(&mut b, r, c, ai);
        let score = -negamax(&b, op, DEPTH - 1, ai);
        if score > best_score {
            best_score = score;
            best = Some((r, c));
        }
    }
    best
}