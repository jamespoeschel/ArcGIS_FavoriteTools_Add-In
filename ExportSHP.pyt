# -*- coding: utf-8 -*-

import arcpy
import os


class Toolbox:
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Export Shapefile"
        self.alias = "exportShapefile"

        # List of tool classes associated with this toolbox
        self.tools = [Tool]


class Tool:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Export Feature to Shapefile"
        self.description = "Exports a feature class or layer to a shapefile in a new folder named after the feature."
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define the tool parameters."""
        
        # Input feature
        feature_to_export = arcpy.Parameter(
            displayName="Feature to Export",
            name="feature_to_export",
            datatype=["DEFeatureClass", "Feature Layer"],
            parameterType="Required",
            direction="Input"
        )

        # Optional output folder
        output_folder = arcpy.Parameter(
            displayName="Output Folder",
            name="output_folder",
            datatype="Folder",
            parameterType="Optional",
            direction="Input"
        )

        # Derived output shapefile
        output_shapefile = arcpy.Parameter(
            displayName="Output Shapefile",
            name="output_shapefile",
            datatype="DEFile",
            parameterType="Derived",
            direction="Output"
        )

        params = [feature_to_export, output_folder, output_shapefile]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Set default output folder suggestion."""
        if not parameters[1].altered:
            home_folder = arcpy.mp.ArcGISProject("CURRENT").homeFolder
            data_folder = os.path.join(home_folder, "DATA")
            if os.path.exists(data_folder):
                parameters[1].value = data_folder
            else:
                parameters[1].value = home_folder
        return

    def execute(self, parameters, messages):
        """Main tool execution."""
        feature = parameters[0].valueAsText
        output_base_folder = parameters[1].valueAsText

        # --- CREATE OUTPUT FOLDER NAMED AFTER FEATURE ---
        new_folder_path = os.path.join(output_base_folder, f"{os.path.basename(feature)}_shp")

        if not os.path.exists(new_folder_path):
            os.makedirs(new_folder_path)

        # --- DEFINE OUTPUT SHAPEFILE PATH ---
        output_shapefile = os.path.join(new_folder_path, f"{os.path.basename(feature)}.shp")

        try:
            arcpy.AddMessage(f"Exporting {feature} to {output_shapefile}...")

            # Perform export
            arcpy.conversion.FeatureClassToShapefile(
                feature,
                new_folder_path
            )

            arcpy.AddMessage(f"✅ Export successful! Shapefile saved to: {output_shapefile}")

        except Exception as e:
            arcpy.AddError(f"❌ Failed to export shapefile. Error: {str(e)}")
            raise

        # Set derived output parameter
        parameters[2].value = output_shapefile

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and added to the display."""
        return
