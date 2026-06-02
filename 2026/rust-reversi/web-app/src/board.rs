// 盤面の定義をまとめるモジュール
pub const SIZE: usize = 8;
pub const EMPTY: u8 = 0;
pub const BLACK: u8 = 1;
pub const WHITE: u8 = 2;
pub type Board = [[u8; SIZE]; SIZE];
