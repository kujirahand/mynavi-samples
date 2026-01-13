<?php
// PHP implementation for receipt generation using GD library
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    header('Location: index.php');
    exit;
}

// 0. Authentication
require_once __DIR__ . '/secrets/config.php';
$submitted_password = $_POST['password'] ?? '';
if ($submitted_password !== RECEIPT_PASSWORD) {
    die('Error: Invalid password.');
}

// 1. Get and Sanitize Input
$date_raw = $_POST['date'] ?? date('Y-m-d');
$address = $_POST['address'] ?? '';
$amount_total = (int)($_POST['amount'] ?? 0);
$proviso = $_POST['proviso'] ?? '';
$tax_rate_val = (int)($_POST['tax_rate'] ?? 10);

// Date formatting
$date_obj = new DateTime($date_raw);
$date_str = $date_obj->format('Y年m月d日');

// 2. Calculations
// Amount is tax-included. 
// Tax Excluded = Total / (1 + Rate/100)
$tax_excluded = floor($amount_total / (1 + ($tax_rate_val / 100)));
$tax_amount = $amount_total - $tax_excluded;

// 3. Setup Paths
$template_path = __DIR__ . '/template.png';
$font_path = __DIR__ . '/ipaexg.ttf';

if (!file_exists($template_path) || !file_exists($font_path)) {
    die('Required files (template.png or ipaexm.ttf) are missing.');
}

// 4. Load Image
$image = imagecreatefrompng($template_path);
if (!$image) {
    die('Failed to load template image.');
}

// 5. Setup Colors and Font Size
$black = imagecolorallocate($image, 0, 0, 0);

// Helper function to draw text
function draw_text($image, $size, $angle, $x, $y, $color, $font, $text) {
    return imagettftext($image, $size, $angle, $x, $y, $color, $font, $text);
}

// 6. Draw Data
// Load coordinates from plot.json
$plot_path = __DIR__ . '/plot.json';
$coords = [];
if (file_exists($plot_path)) {
    $coords = json_decode(file_get_contents($plot_path), true) ?: [];
}

// Fallback values if JSON is missing or incomplete
$c_date = $coords['date'] ?? ['x' => 913, 'y' => 135, 'size' => 35];
$c_to_name = $coords['to_name'] ?? ['x' => 151, 'y' => 167, 'size' => 50];
$c_amnt = $coords['amount'] ?? ['x' => 161, 'y' => 322, 'size' => 60];
$c_prov = $coords['proviso'] ?? ['x' => 680, 'y' => 340, 'size' => 30];
$c_tax  = $coords['tax_info'] ?? ['x' => 162, 'y' => 433, 'size' => 22, 'line_height' => 40];

// Date
draw_text($image, $c_date['size'], 0, $c_date['x'], $c_date['y'], $black, $font_path, $date_str);

// Address
draw_text($image, $c_to_name['size'], 0, $c_to_name['x'], $c_to_name['y'], $black, $font_path, $address . ' 様');

// Amount
$amount_formatted = '￥' . number_format($amount_total) . '-';
draw_text($image, $c_amnt['size'], 0, $c_amnt['x'], $c_amnt['y'], $black, $font_path, $amount_formatted);

// Proviso
draw_text($image, $c_prov['size'], 0, $c_prov['x'], $c_prov['y'], $black, $font_path, '但し ' . $proviso);

// Tax Info
$tax_info_y = $c_tax['y'];
$line_height = $c_tax['line_height'];
draw_text($image, $c_tax['size'], 0, $c_tax['x'], $tax_info_y, $black, $font_path, "(内消費税等 ￥" . number_format($tax_amount) . ")");
draw_text($image, $c_tax['size'], 0, $c_tax['x'], $tax_info_y + $line_height, $black, $font_path, "税率: " . $tax_rate_val . "%");
draw_text($image, $c_tax['size'], 0, $c_tax['x'], $tax_info_y + $line_height * 2, $black, $font_path, "税抜金額: ￥" . number_format($tax_excluded));

// 7. Save to History and CSV
$history_dir = __DIR__ . '/history';
$secrets_dir = __DIR__ . '/secrets';
$csv_path = $secrets_dir . '/history.csv';

// Create directories if they don't exist
if (!is_dir($history_dir)) mkdir($history_dir, 0755, true);
if (!is_dir($secrets_dir)) mkdir($secrets_dir, 0755, true);

// Generate unique ID
$id = date('Ymd-His') . '-' . uniqid();
$save_path = $history_dir . '/' . $id . '.png';

// Save image to file
imagepng($image, $save_path);

// Save to CSV
$csv_data = [
    $id,
    $date_raw,
    $address,
    $amount_total,
    $proviso,
    $tax_rate_val,
    $tax_excluded,
    $tax_amount,
    date('Y-m-d H:i:s')
];
$fp = fopen($csv_path, 'a');
fputcsv($fp, $csv_data, ",", "\"", "\\");
fclose($fp);

// 8. Output Image
header('Content-Type: image/png');
header('Content-Disposition: inline; filename="receipt_' . $id . '.png"');
imagepng($image);

// 9. Cleanup
imagedestroy($image);
