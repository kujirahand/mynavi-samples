// file: ai.rs --- 評価関数ベースのシンプルAIモジュール
use crate::board::{Board, BLACK, WHITE};
use crate::rules::{apply_move, valid_moves};

// 盤面の重みを定義する。角が高く、辺もある程度高い。 --- (*1)
const W: [[i32; 8]; 8] = [
    [30,-12, 0,-1,-1, 0,-12,30],
    [-12,-15,-3,-3,-3,-3,-15,-12],
    [0, -3, 0,-1,-1, 0, -3, 0],
    [-1,-3, -1,-1,-1,-1, -3,-1],
    [-1,-3, -1,-1,-1,-1, -3,-1],
    [0, -3, 0,-1,-1, 0, -3, 0],
    [-12,-15,-3,-3,-3,-3,-15,-12],
    [30,-12, 0,-1,-1, 0,-12,30],
];

// 局面の重み付き合計を計算する --- (*2)
fn positional_score(board: &Board, me: u8) -> i32 {
    let opp = if me == BLACK { WHITE } else { BLACK };
    let mut s = 0;
    for r in 0..8 {
        for c in 0..8 {
            if board[r][c] == me { s += W[r][c]; }
            if board[r][c] == opp { s -= W[r][c]; }
        }
    }
    s
}

// 重みと合法手数を使って局面を評価する --- (*3)
pub fn evaluate(board: &Board, me: u8) -> i32 {
    let mobility = valid_moves(board, me).len() as i32;
    let opp = if me == BLACK { WHITE } else { BLACK };
    let opp_mobility = valid_moves(board, opp).len() as i32;
    positional_score(board, me) + (mobility - opp_mobility) * 2
}

// 1手先を読んで最も評価値が高い手を返す --- (*4)
pub fn choose_move(board: &Board, ai: u8) -> Option<(usize, usize)> {
    let moves = valid_moves(board, ai);
    let mut best: Option<(usize, usize, i32)> = None;
    for (r, c) in moves {
        let mut b = *board;
        apply_move(&mut b, r, c, ai);
        let score = evaluate(&b, ai);
        if best.is_none() || score > best.unwrap().2 { best = Some((r, c, score)); }
    }
    best.map(|(r, c, _)| (r, c))
}