// 盤面の定義と関連関数をまとめたモジュール
pub const SIZE: usize = 8; // 盤面のサイズ (8x8)
// 石の状態を表す定数
pub const EMPTY: u8 = 0; 
pub const BLACK: u8 = 1;
pub const WHITE: u8 = 2;
// Boardは8x8の2次元配列で、各セルはEMPTY, BLACK, WHITEのいずれか。
pub type Board = [[u8; SIZE]; SIZE];

// 初期配置の盤面を作って返す。
pub fn new_board() -> Board {
    // 8x8 を 0(空)で初期化し、中央4マスだけ配置する。
    let mut b = [[EMPTY; SIZE]; SIZE];
    b[3][3] = WHITE;
    b[3][4] = BLACK;
    b[4][3] = BLACK;
    b[4][4] = WHITE;
    b
}

// プレイヤー番号を表示用の日本語名に変換する。
pub fn stone_name(player: u8) -> &'static str {
    if player == BLACK { "黒" } else { "白" }
}

// 指定した石の数を盤面全体から数える。
pub fn count_stones(board: &Board, stone: u8) -> usize {
    board.iter().flatten().filter(|&&v| v == stone).count()
}

// 盤面をA-H, 1-8の座標付きで表示する。
pub fn print_board(board: &Board) {
    // Excel風に列をA-H、行を1-8で表示する。
    println!("   A B C D E F G H");
    for (r, row) in board.iter().enumerate() {
        print!("{:>2} ", r + 1);
        for &cell in row {
            let ch = match cell {
                BLACK => '●',
                WHITE => '○',
                _ => '.',
            };
            print!("{} ", ch);
        }
        println!();
    }
}