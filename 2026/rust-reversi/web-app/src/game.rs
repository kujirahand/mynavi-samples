// 手番を扱う小さな関数
use crate::board::{BLACK, WHITE};

// 相手の石を返す。
pub fn opponent(p: u8) -> u8 {
    if p == BLACK { WHITE } else { BLACK }
}
