// 福島県浜通り（相馬市・南相馬市周辺の農地）
var roi = ee.Geometry.Rectangle([140.85, 37.55, 141.02, 37.80]);

// =========================================================================
// 1. 光学（Sentinel-2）：NDVIピーク抽出
// =========================================================================
var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(roi)
  .filterDate('2024-06-01', '2024-08-31')
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30)); // 雲量閾値を少し緩和

var ndvi_max = s2.map(function(img) {
  return img.normalizedDifference(['B8', 'B4']).rename('NDVI');
}).max().clip(roi);

// =========================================================================
// 2. SAR（Sentinel-1）：軌道統一と期間拡大
// =========================================================================
var s1 = ee.ImageCollection('COPERNICUS/S1_GRD')
  .filterBounds(roi)
  // 【対策1】観測周期（12日）を考慮し、期間を7月1日〜8月31日に拡大
  .filterDate('2024-07-01', '2024-08-31')
  .filter(ee.Filter.eq('instrumentMode', 'IW'))
  // 【対策2】このエリアで安定して取得できる軌道（DESCENDING または ASCENDING）に設定
  .filter(ee.Filter.eq('orbitProperties_pass', 'DESCENDING')); 

// 枚数チェック用（Consoleタブに出力）
print('S2 該当枚数:', s2.size());
print('S1 該当枚数:', s1.size());

var s1_vh_mean = s1.select('VH').mean().clip(roi);
var s1_vv_mean = s1.select('VV').mean().clip(roi);

// =========================================================================
// 3. 休耕地判定（空画像エラーの回避処理付き）
// =========================================================================
// NDVIとS1の条件判定
var fallow_mask = ndvi_max.lt(0.40)
  .and(s1_vh_mean.lt(-15.0));

// =========================================================================
// 4. 可視化設定
// =========================================================================
Map.centerObject(roi, 12);

Map.addLayer(ndvi_max, {min: 0.0, max: 0.8, palette: ['blue', 'white', 'green']}, 'NDVI Max (B8/B4)');
Map.addLayer(s1_vh_mean, {min: -25, max: -5}, 'SAR VH Mean');

// マスクが存在する場合のみ赤色で表示
Map.addLayer(fallow_mask.updateMask(fallow_mask), {palette: ['red']}, '休耕地疑い');