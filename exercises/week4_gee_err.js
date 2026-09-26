// 福島県浜通り（相馬市・南相馬市周辺の農地）
var roi = ee.Geometry.Rectangle([140.85, 37.55, 141.02, 37.80]);

// --- 1. 光学（Sentinel-2）：NDVIピーク抽出 ---
var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(roi)
  .filterDate('2024-06-01', '2024-08-31')
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20));

// 【罠①】B5(Red Edge)でNDVIを計算しており、大区画農地でも植生値が過小評価される
var ndvi_max = s2.map(function(img) {
  return img.normalizedDifference(['B5', 'B4']).rename('NDVI');
}).max().clip(roi);

// --- 2. SAR（Sentinel-1）：時系列変化量 ---
var s1 = ee.ImageCollection('COPERNICUS/S1_GRD')
  .filterBounds(roi)
  .filterDate('2024-08-01', '2024-08-31')
  .filter(ee.Filter.eq('instrumentMode', 'IW'));
  // 【罠②】昇交/降交（ASCENDING/DESCENDING）が混在し、大区画農地の端で影・角度歪みが生じる

var s1_vh_mean = s1.select('VH').mean().clip(roi);

// --- 3. 疑似ラベルによる「休耕地判定」 ---
// 【罠③】すでにdB値のS1に不要な10*log10を適用、かつ判定閾値の物理的ロジックが破綻
var fallow_mask = ndvi_max.lt(0.35).and(s1_vh_mean.log10().multiply(10).lt(-20));

// --- 4. 可視化 ---
Map.centerObject(roi, 12);
Map.addLayer(ndvi_max, {min: 0, max: 0.8, palette: ['blue', 'white', 'green']}, 'NDVI Max (罠①)');
Map.addLayer(s1_vh_mean, {min: -25, max: -5}, 'SAR VH Mean (罠②)');
Map.addLayer(fallow_mask.updateMask(fallow_mask), {palette: ['red']}, '休耕地疑い (罠③)');