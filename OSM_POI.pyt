import arcpy
import requests

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the .pyt file is its name)."""
        self.label = "OSM Overpass Toolbox"
        self.alias = "osmtools"
        self.tools = [OSMOverpassPOI]

class OSMOverpassPOI(object):
    def __init__(self):
        self.label = "Extract OSM POIs"
        self.description = "Retrieves points of interest from OpenStreetMap for a named place and creates a feature class."

    def getParameterInfo(self):
        params = []

        param0 = arcpy.Parameter(
            displayName="Geography Name",
            name="place_name",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )

        param1 = arcpy.Parameter(
            displayName="Output Feature Class Name",
            name="output_name",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )

        param1.value = "OSM_POIs"

        params = [param0, param1]
        return params

    def isLicensed(self):
        return True

    def execute(self, parameters, messages):
        place_name = parameters[0].valueAsText
        output_name = parameters[1].valueAsText

        arcpy.env.overwriteOutput = True

        aprx = arcpy.mp.ArcGISProject("CURRENT")
        default_gdb = aprx.defaultGeodatabase
        output_fc = f"{default_gdb}\\{parameters[1].valueAsText}"

        def get_osm_area_id(place):
            url = "https://nominatim.openstreetmap.org/search"
            params = {
                'q': place,
                'format': 'json',
                'addressdetails': 1,
                'extratags': 1,
            }
            headers = {'User-Agent': 'ArcGISOverpassTool/1.0'}
            response = requests.get(url, params=params, headers=headers)
            data = response.json()

            if not data:
                raise ValueError("Place not found in Nominatim.")

            osm_type = data[0]['osm_type']
            osm_id = int(data[0]['osm_id'])

            if osm_type == 'relation':
                area_id = 3600000000 + osm_id
            elif osm_type == 'node':
                area_id = 3600000000 + osm_id
            else:
                raise ValueError("Unsupported OSM type.")

            return area_id

        try:
            area_id = get_osm_area_id(place_name)
        except Exception as e:
            arcpy.AddError(f"Error getting OSM area ID: {e}")
            return

        tags = {
            'amenity': [
                'school', 'college', 'library', 'fire_station', 'hospital', 'clinic', 'place_of_worship',
                'community_centre', 'townhall', 'public_building',
                'restaurant', 'fast_food', 'cafe' 
            ],
            'leisure': [
                'sports_centre', 'fitness_centre', 'club'
            ],
            'office': [
                'government', 'administrative', 'civil'
            ],
            'shop': [
                'supermarket', 'mall'
            ],
            'aeroway': [
                'aerodrome', 'airport'
            ]
        }

        query_parts = []
        for key, values in tags.items():
            for value in values:
                query_parts.append(f'node["{key}"="{value}"](area:{area_id});')
                query_parts.append(f'relation["{key}"="{value}"](area:{area_id});')

        query = f"""
        [out:json][timeout:25];
        (
          {"".join(query_parts)}
        );
        out center;
        """

        overpass_url = "http://overpass-api.de/api/interpreter"

        try:
            response = requests.get(overpass_url, params={'data': query})
            data = response.json()
        except Exception as e:
            arcpy.AddError(f"Error contacting Overpass API: {e}")
            return

        poi_points = []
        for element in data.get('elements', []):
            tags_in_element = element.get('tags', {})
            name = tags_in_element.get('name', 'Unnamed')

            poi_type = "Unknown"
            for key, values in tags.items():
                if key in tags_in_element and tags_in_element[key] in values:
                    poi_type = tags_in_element[key]
                    break

            if element['type'] == 'node':
                geom_source = 'point'
                lon = element.get('lon')
                lat = element.get('lat')
            elif element['type'] == 'way':
                geom_source = 'polygon'
                center = element.get('center')
                if center:
                    lon = center.get('lon')
                    lat = center.get('lat')
                else:
                    continue
            else:
                continue

            poi_points.append((name, poi_type, lon, lat, geom_source))

        if poi_points:
            spatial_ref = arcpy.SpatialReference(4326)
            arcpy.management.CreateFeatureclass(
                out_path=default_gdb,
                out_name=output_name,
                geometry_type="POINT",
                spatial_reference=spatial_ref
            )

            arcpy.management.AddField(output_fc, "Name", "TEXT", field_length=255)
            arcpy.management.AddField(output_fc, "Type", "TEXT", field_length=255)
            arcpy.management.AddField(output_fc, "Geom_Source", "TEXT", field_length=50)

            with arcpy.da.InsertCursor(output_fc, ["SHAPE@XY", "Name", "Type", "Geom_Source"]) as cursor:
                for name, poi_type, lon, lat, geom_source in poi_points:
                    cursor.insertRow([(lon, lat), name, poi_type, geom_source])

            active_map = aprx.activeMap
            layer = active_map.addDataFromPath(output_fc)

            sym = layer.symbology
            sym.updateRenderer('UniqueValueRenderer')
            sym.renderer.fields = ['Type']
            layer.symbology = sym

            arcpy.AddMessage(f"Created feature class: {output_fc} with {len(poi_points)} POIs and added to the map.")
        else:
            arcpy.AddWarning(f"No POIs found for the given tags in {place_name}.")

