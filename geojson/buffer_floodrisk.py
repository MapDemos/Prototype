import geopandas as gpd
from shapely.geometry import shape, mapping
import json

# Load GeoJSON data
with open('flood_risk_20191012060000.geojson') as f:
    data = json.load(f)

# Convert GeoJSON to GeoDataFrame
gdf = gpd.GeoDataFrame.from_features(data['features'])

# Ensure the GeoDataFrame has the correct CRS (assuming WGS84)
gdf.set_crs(epsg=4326, inplace=True)

# Buffer the features (1 km radius)
# Convert the GeoDataFrame to Web Mercator CRS (EPSG:3857) for accurate buffering
gdf = gdf.to_crs(epsg=3857)  # Web Mercator projection
gdf['geometry'] = gdf['geometry'].buffer(1000)  # Buffer by 1000 meters (1 km)

# Convert back to WGS84 CRS
gdf = gdf.to_crs(epsg=4326)

# Convert back to GeoJSON
buffered_geojson = json.loads(gdf.to_json())

# Save the buffered GeoJSON to a file
with open('buffered_flood_risk_20191012060000.geojson', 'w') as f:
    json.dump(buffered_geojson, f)