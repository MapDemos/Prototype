import xml.etree.ElementTree as ET
import geojson
import re

# Load and parse the XML file
file_name = '20241110012447_0_VPTW63_010000.xml'
file_path = './xml/' + file_name  # Ensure this path is correct
tree = ET.parse(file_path)
root = tree.getroot()

# Function to parse the coordinates and create a GeoJSON Point feature
def create_point_feature(base_point, properties):
    # Ignore BasePoint elements with type "中心位置（度）"
    if base_point.attrib.get('type') == "中心位置（度）":
        return None

    coords = base_point.text.strip().split('+')
    if len(coords) >= 3:
        try:
            # Skip the first element if it's empty
            if coords[0] == '':
                coords = coords[1:]

            # Remove any trailing slashes from the coordinate strings
            lat_str = coords[0].replace('/', '')
            lon_str = coords[1].replace('/', '')

            def parse_coord(coord_str):
                if '.' in coord_str:
                    return float(coord_str)
                else:
                    return float(coord_str[:-2] + '.' + coord_str[-2:])

            lat = parse_coord(lat_str)
            lon = parse_coord(lon_str)

            point = geojson.Point((lon, lat))
            
            # Add point_type property from the type attribute of BasePoint
            properties['point_type'] = base_point.attrib.get('type', '')

            feature = geojson.Feature(geometry=point, properties=properties)
            return feature
        except ValueError:
            # Handle conversion error if coordinates are not valid
            print(f"Invalid coordinates found: {coords}")
    return None

# Function to collect all properties and attributes from the XML element
def collect_properties(element):
    properties = {}
    # Include attributes
    for attr_name, attr_value in element.attrib.items():
        if attr_name == 'type' and element.tag.endswith('DateTime'):
            # Special handling for DateTime type attribute
            properties['type'] = attr_value
        else:
            properties[attr_name] = attr_value
    # Include text and child elements
    for child in element:
        tag = child.tag.split('}')[1]  # Remove namespace
        # Special handling for DateTime element
        if tag == 'DateTime':
            properties['DateTime'] = child.text
            if 'type' in child.attrib:
                properties['type'] = child.attrib['type']
        else:
            # Build a unique key using available attributes
            attr_type = child.attrib.get('type')
            attr_unit = child.attrib.get('unit')
            attr_condition = child.attrib.get('condition')

            unique_key_parts = [tag]
            if attr_type:
                unique_key_parts.append(attr_type)
            if attr_unit:
                unique_key_parts.append(attr_unit)
            if attr_condition:
                unique_key_parts.append(attr_condition)

            unique_key = "_".join(unique_key_parts)

            if len(child):
                child_properties = collect_properties(child)
                for key, value in child_properties.items():
                    properties[f"{unique_key}_{key}"] = value
            else:
                properties[unique_key] = child.text
    return properties

# Initialize a list to hold GeoJSON features
features = []

# Iterate through the XML structure to find relevant geographic information
for meteorological_info in root.findall(".//{http://xml.kishou.go.jp/jmaxml1/body/meteorology1/}MeteorologicalInfo"):
    # Collect properties for the feature
    properties = collect_properties(meteorological_info)
    
    # Find base points and create GeoJSON features
    for base_point in meteorological_info.findall(".//{http://xml.kishou.go.jp/jmaxml1/elementBasis1/}BasePoint"):
        feature = create_point_feature(base_point, properties)
        if feature:
            features.append(feature)

# Create a GeoJSON FeatureCollection
feature_collection = geojson.FeatureCollection(features)

# Save the GeoJSON to a file with UTF-8 encoding
output_file_path = './json/' + file_name.replace('.xml', '.geojson')
with open(output_file_path, 'w', encoding='utf-8') as f:
    geojson.dump(feature_collection, f, ensure_ascii=False)

print(f"GeoJSON file created successfully at {output_file_path}.")
