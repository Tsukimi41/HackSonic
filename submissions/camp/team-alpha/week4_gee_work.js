// =========================================================================
// camp-alpha / W4 スカベンジャーハント 修正版＋検証
//
// 原本: exercises/week4_gee_err.js（罠入り）
// 罠3つを修正し、修正の効果を数値で確認する検証出力を追加した版。
// 実測値と考察は analysis_doc.md の 7. に記録。
//
//   [x] 罠① NDVI の NIR に B5（Red Edge）を誤用 → B8 に修正
//   [x] 罠② 軌道方向の統一なし → orbitProperties_pass = DESCENDING に統一
//   [x] 罠③ dB の S1_GRD に 10*log10() を二重適用 → 削除し dB のまま閾値判定
//
// 修正前の実測値: 休耕判定 = ROI全域で0件（エラーも警告も出ないまま機能停止）
// 修正後の実測値: 休耕判定 = 5,119件（scale 100 なので 5,119 ha ≒ 51.2 km²）
// =========================================================================

// 福島県浜通り（相馬市・南相馬市周辺の農地）
var roi = ee.Geometry.Rectangle([140.85, 37.55, 141.02, 37.80]);

// 検証用の基準地点（Inspector のクリックでは同一ピクセルを再現できないため座標で固定）
var pt = ee.Geometry.Point([140.93508, 37.60020]);   // 地点3

// =========================================================================
// 1. 光学（Sentinel-2）：NDVIピーク抽出
// =========================================================================
var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(roi)
  .filterDate('2024-06-01', '2024-08-31')
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20));

// 【罠①修正】NIR は B8(842nm)。B5(705nm) はレッドエッジの立ち上がり途中で
// 葉の海綿状組織による強い構造反射を捉えないため、NDVI が 0.20〜0.28 過小に出る。
var ndvi_max = s2.map(function(img) {
  return img.normalizedDifference(['B8', 'B4']).rename('NDVI');
}).max().clip(roi);

// =========================================================================
// 2. SAR（Sentinel-1）：軌道統一・期間拡大・スペックル低減
// =========================================================================
var s1 = ee.ImageCollection('COPERNICUS/S1_GRD')
  .filterBounds(roi)
  // 【修正】8月のみでは DESCENDING が3枚しかなく median の効果が弱い。
  // 回帰周期12日を踏まえ 7/1 まで遡って枚数を確保する。
  .filterDate('2024-07-01', '2024-08-31')
  .filter(ee.Filter.eq('instrumentMode', 'IW'))
  // 【罠②修正】入射角が揃わないと σ⁰ が観測ごとに揺れ、湛水と乾燥を誤読する。
  // 実測ではこのROI・この期間に ASCENDING が0枚のため DESCENDING に統一。
  .filter(ee.Filter.eq('orbitProperties_pass', 'DESCENDING'));

// 【修正】mean → median。スペックルは外れ値として乗るため中央値の方が頑健。
var s1_vh_med = s1.select('VH').median().clip(roi);

// =========================================================================
// 3. 疑似ラベルによる「休耕地判定」
// =========================================================================
// 【罠③修正】COPERNICUS/S1_GRD は既に dB（σ⁰）で値は負。
// 負数の log10() は定義域外で GEE がマスクし、そのマスクが .and() まで伝播するため
// 修正前は ROI 全域で判定が成立していなかった。dB のまま閾値判定する。
var fallow_mask = ndvi_max.lt(0.40).and(s1_vh_med.lt(-15.0));

// =========================================================================
// 4. 検証出力（Console タブで確認する）
// =========================================================================

// --- 4-1. データ枚数と軌道の内訳 ---
print('S2 該当枚数:', s2.size());
print('S1 該当枚数:', s1.size());
print('軌道の内訳:', s1.aggregate_histogram('orbitProperties_pass'));

// --- 4-2. 判定が機能しているか（修正前は 0 件だった）---
print('休耕判定に該当したピクセル数:', fallow_mask.selfMask().reduceRegion({
  reducer: ee.Reducer.count(),
  geometry: roi,
  scale: 100,
  maxPixels: 1e9
}));

// --- 4-3. 罠①の影響を同一座標で切り分ける ---
// 検証専用。B5 版の NDVI を再現して同じピクセルで比較する。
var ndvi_b5 = s2.map(function(img) {
  return img.normalizedDifference(['B5', 'B4']).rename('NDVI_B5');
}).max().clip(roi);

print('地点3 NDVI(B5/B4・罠あり):', ndvi_b5.reduceRegion({
  reducer: ee.Reducer.first(), geometry: pt, scale: 10}));
print('地点3 NDVI(B8/B4・正しい):', ndvi_max.reduceRegion({
  reducer: ee.Reducer.first(), geometry: pt, scale: 10}));

// --- 4-4. 前処理変更（mean→median・期間拡大）の影響を同一座標で切り分ける ---
var s1_old = ee.ImageCollection('COPERNICUS/S1_GRD')
  .filterBounds(roi)
  .filterDate('2024-08-01', '2024-08-31')
  .filter(ee.Filter.eq('instrumentMode', 'IW'));

print('地点3 VH 修正前 mean(8月・3枚):', s1_old.select('VH').mean().reduceRegion({
  reducer: ee.Reducer.first(), geometry: pt, scale: 10}));
print('地点3 VH 修正後 median(7-8月・5枚):', s1_vh_med.reduceRegion({
  reducer: ee.Reducer.first(), geometry: pt, scale: 10}));

// --- 4-5. 休耕判定の土地被覆別内訳（市街地の誤検出を定量化）---
// 地図を見ると赤いピクセルが市街地・道路をトレースしている。
// 平滑な舗装面・屋根は鏡面反射で VH が暗く、NDVI も低いため条件を満たしてしまう。
// クラス番号: 10樹林 30草地 40農地 50市街地 60裸地 80水域
// ※ データセットIDでエラーが出る場合は ee.Image('ESA/WorldCover/v200/2021') を試す
var lc = ee.ImageCollection('ESA/WorldCover/v200').first().select('Map');

print('休耕判定の土地被覆別ピクセル数:', lc.updateMask(fallow_mask).reduceRegion({
  reducer: ee.Reducer.frequencyHistogram(),
  geometry: roi,
  scale: 100,
  maxPixels: 1e9
}));

// 参考: ROI 全体の土地被覆内訳（母数として比較する）
print('ROI全体の土地被覆別ピクセル数:', lc.clip(roi).reduceRegion({
  reducer: ee.Reducer.frequencyHistogram(),
  geometry: roi,
  scale: 100,
  maxPixels: 1e9
}));

// =========================================================================
// 5. 可視化
// =========================================================================
Map.centerObject(roi, 12);
Map.addLayer(ndvi_max, {min: 0, max: 0.9, palette: ['blue', 'white', 'green']}, 'NDVI Max (B8/B4)');
Map.addLayer(s1_vh_med, {min: -25, max: -5}, 'SAR VH Median (DESC)');
Map.addLayer(fallow_mask.updateMask(fallow_mask), {palette: ['red']}, '休耕地疑い');

// 誤検出の目視確認用（初期は非表示。チェックを入れて赤との重なりを見る）
Map.addLayer(lc.eq(50).selfMask().clip(roi), {palette: ['blue']},   '参照: 市街地 (WorldCover 50)', false);
Map.addLayer(lc.eq(40).selfMask().clip(roi), {palette: ['yellow']}, '参照: 農地 (WorldCover 40)', false);
Map.addLayer(pt, {color: 'black'}, '検証地点3', false);
