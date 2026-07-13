use lopdf::Document;
use std::env;

fn main() {
    // コマンドライン引数から「入力ファイル」と「分割ページ数」を取得 --- (※1)
    let args: Vec<String> = env::args().collect();
    let input = &args[1];
    let pages_per_file: u32 = args[2].parse().unwrap();

    // PDFを読み込み、総ページ数を取得 --- (※2)
    let doc = Document::load(input).unwrap();
    let total_pages = doc.get_pages().len() as u32;

    // 指定ページ数ごとに分割して保存 --- (※3)
    let mut start = 1;
    let mut file_no = 1;
    while start <= total_pages {
        // 分割するページ範囲を計算 --- (※4)
        let end = (start + pages_per_file - 1).min(total_pages);

        // 元のPDFを複製し、対象範囲外のページを削除 --- (※5)
        let mut part = doc.clone();
        let remove_pages: Vec<u32> = (1..=total_pages).filter(|p| *p < start || *p > end).collect();
        part.delete_pages(&remove_pages);
        part.prune_objects();

        // ファイル名を生成して保存 --- (※6)
        let output = format!("output_{file_no}.pdf");
        part.save(&output).unwrap();
        println!("{output} を保存しました（{start}〜{end}ページ）");

        start = end + 1;
        file_no += 1;
    }
}
