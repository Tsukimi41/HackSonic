collection = (
    ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    .filterDate('2024-10-01', '2024-10-31')
    .filterBounds(roi)
    .filterMetadata('CLOUDY_PIXEL_PERCENTAGE', 'less_than', 20)
)

image = collection.sort('CLOUDY_PIXEL_PERCENTAGE').first()

ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')

m = geemap.Map()
collection = (
    ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    .filterDate('2024-10-10', '2024-10-15')
    .filterBounds(roi)
    .filterMetadata('CLOUDY_PIXEL_PERCENTAGE', 'less_than', 20)
)

m.add_basemap("SATELLITE")

# この行はコメントアウト
# m.add_layer(image, rgb_vis, 'Sentinel-2 RGB')

m.add_layer(ndvi, ndvi_vis, 'NDVI')

m.center_object(roi, 13)

m

stats = ndvi.reduceRegion(
    reducer=ee.Reducer.mean(),
    geometry=roi,
    scale=10,
    bestEffort=True
)

print(stats.getInfo())

#出力は{'NDVI_max': 1, 'NDVI_min': -0.7414965986394558}であった

#出力は{'NDVI': 0.3672796598938571}であった