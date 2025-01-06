import geopandas as gpd
import pandas as pd
from shapely.geometry import shape, mapping
import json
from rtree import index

# Load GeoJSON data
with open('buffered_flood_risk_20191012060000.geojson') as f:
    flood_risk_data = json.load(f)

with open('camera_scam_portal.geojson') as f:
    camera_scam_data = json.load(f)

with open('camera_cctv_portal.geojson') as f:
    camera_cctv_data = json.load(f)

# Convert GeoJSON to GeoDataFrame
flood_risk_gdf = gpd.GeoDataFrame.from_features(flood_risk_data['features'])
camera_scam_gdf = gpd.GeoDataFrame.from_features(camera_scam_data['features'])
camera_cctv_gdf = gpd.GeoDataFrame.from_features(camera_cctv_data['features'])

# Ensure the GeoDataFrames have the correct CRS (assuming WGS84)
flood_risk_gdf.set_crs(epsg=4326, inplace=True)
camera_scam_gdf.set_crs(epsg=4326, inplace=True)
camera_cctv_gdf.set_crs(epsg=4326, inplace=True)

# Create spatial index for flood risk geometries
flood_risk_idx = index.Index()
for pos, geom in enumerate(flood_risk_gdf.geometry):
    flood_risk_idx.insert(pos, geom.bounds)

# Function to update FLOODRISK property
def update_floodrisk(camera_gdf, flood_risk_gdf, flood_risk_idx):
    # Ensure the FLOODRISK column exists and initialize to 0 if it does not
    if 'FLOODRISK' not in camera_gdf.columns:
        camera_gdf['FLOODRISK'] = 0

    for idx, camera in camera_gdf.iterrows():
        possible_matches_index = list(flood_risk_idx.intersection(camera.geometry.bounds))
        possible_matches = flood_risk_gdf.iloc[possible_matches_index]
        for _, flood_risk in possible_matches.iterrows():
            if camera.geometry.within(flood_risk.geometry):
                if flood_risk['TYPE'] == "1":
                    flood_risk_value = flood_risk['FLOODRISK']
                elif flood_risk['TYPE'] == "2":
                    flood_risk_value = flood_risk['FLOODFCST']
                else:
                    continue

                if flood_risk_value is not None:
                    flood_risk_value = int(flood_risk_value)
                    current_flood_risk = int(camera_gdf.at[idx, 'FLOODRISK'])
                    camera_gdf.at[idx, 'FLOODRISK'] = max(current_flood_risk, flood_risk_value)
    return camera_gdf

# Update FLOODRISK property for both camera datasets
camera_scam_gdf = update_floodrisk(camera_scam_gdf, flood_risk_gdf, flood_risk_idx)
camera_cctv_gdf = update_floodrisk(camera_cctv_gdf, flood_risk_gdf, flood_risk_idx)

# Combine the updated camera datasets
camera_all_gdf = gpd.GeoDataFrame(pd.concat([camera_scam_gdf, camera_cctv_gdf], ignore_index=True))

# Convert back to GeoJSON
camera_all_geojson = json.loads(camera_all_gdf.to_json())

# Save the updated GeoJSON to a new file
with open('camera_all_20191012060000.geojson', 'w') as f:
    json.dump(camera_all_geojson, f)