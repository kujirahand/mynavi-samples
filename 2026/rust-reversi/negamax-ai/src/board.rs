// 盤面の定義と表示を担当するモジュール
pub const SIZE: usize = 8;
pub const EMPTY: u8 = 0;
pub const BLACK: u8 = 1;
pub const WHITE: u8 = 2;
pub type Board = [[u8; SIZE]; SIZE];

// 初期配置の盤面を作る。
pub fn new_board() -> Board {
    let mut b = [[EMPTY; SIZE]; SIZE];
    b[3][3] = WHITE;
    b[3][4] = BLACK;
    b[4][3] = BLACK;
    b[4][4] = WHITE;
    b
}

// プレイヤー番号を表示名に変換する。
pub fn stone_name(player: u8) -> &'static str {
    if player == BLACK { "黒" } else { "白" }
}

// 石の数を数える。
pub fn count_stones(board: &Board, stone: u8) -> usize {
    board.iter().flatten().filter(|&&v| v == stone).count()
}

// 盤面をA-H, 1-8で表示する。
pub fn print_board(board: &Board) {
    println!("   A B C D E F G H");
    for (r, row) in board.iter().enumerate() {
        print!("{:>2} ", r + 1);
        for &cell in row {
            let ch = match cell { BLACK => '●', WHITE => '○', _ => '.' };
            print!("{} ", ch);
        }
        println!();
    }
}