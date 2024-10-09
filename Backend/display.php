<?php
// 启用错误报告
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);

/**
 * Convert a set of NZTM2000 (EPSG:2193) coordinates to WGS84 (EPSG:4326).
 * Assumes that the input is in meters (NZTM2000 coordinate system).
 */

// NZTM2000 到 WGS84 的转换参数（近似）
$origin_lat = -41.0000;  // 原点纬度（NZTM2000 的参考纬度）
$origin_lon = 173.0000;  // 原点经度（NZTM2000 的参考经度）
$false_easting = 1600000;  // 偏移量（NZTM2000 的 X 轴起点）
$false_northing = 10000000;  // 偏移量（NZTM2000 的 Y 轴起点）

// 平面坐标到经纬度转换的函数
function convertNZTMToWGS84($easting, $northing) {
    global $origin_lat, $origin_lon, $false_easting, $false_northing;

    // 计算偏移后的坐标
    $x = $easting - $false_easting;
    $y = $northing - $false_northing;

    // 输出调试信息
    echo "Input easting: $easting, northing: $northing\n";
    echo "Offset x: $x, y: $y\n";

    // 简单的投影转换（注意：实际转换应该使用复杂投影公式）
    $latitude = $origin_lat + ($y / 111320);  // 1米大约为 1/111320 度纬度
    $longitude = $origin_lon + ($x / (111320 * cos(deg2rad($origin_lat))));  // 考虑经度的缩放因子

    return [$latitude, $longitude];
}

// 定义 MULTIPOLYGON 的平面坐标 (米为单位 - NZTM2000)
$multiPolygon = [
    [
        [1225000, 4793000],
        [1225000, 4794000],
        [1226000, 4794000],
        [1226000, 4793000],
        [1225000, 4793000]  // 闭合点
    ]
];

// 转换 MULTIPOLYGON 中的每个点
$convertedMultiPolygon = [];
foreach ($multiPolygon as $polygon) {
    $convertedPolygon = [];
    foreach ($polygon as $coord) {
        list($converted_lat, $converted_lon) = convertNZTMToWGS84($coord[0], $coord[1]);
        $convertedPolygon[] = [$converted_lat, $converted_lon];
    }
    $convertedMultiPolygon[] = $convertedPolygon;
}

// 输出转换结果
echo "Converted MULTIPOLYGON (NZTM2000 -> WGS84):\n";
foreach ($convertedMultiPolygon as $polygon) {
    echo "Polygon:\n";
    foreach ($polygon as $point) {
        echo "Latitude: " . $point[0] . ", Longitude: " . $point[1] . "\n";
    }
}
?>
