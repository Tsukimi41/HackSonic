collection = (
    ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    .filterDate('2024-07-01', '2024-07-31')
    .filterBounds(roi)
    .filterMetadata('CLOUDY_PIXEL_PERCENTAGE', 'less_than', 20)
)

image = collection.sort('CLOUDY_PIXEL_PERCENTAGE').first()

ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')

m = geemap.Map()
collection = (
    ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    .filterDate('2024-07-10', '2024-07-15')
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

#出力は{'NDVI': 0.4606119717438873}であった