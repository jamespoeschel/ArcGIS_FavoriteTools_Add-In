# -*- coding: utf-8 -*-

import arcpy


class Toolbox:
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Toolbox"
        self.alias = "toolbox"

        # List of tool classes associated with this toolbox
        self.tools = [Tool]


class Tool:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Unique Values to Features"
        self.description = ""

    def getParameterInfo(self):

        input1 = arcpy.Parameter(
            displayName="Layers",
            name="FeatureLayer1",
            datatype=["GPFeatureLayer", "Feature Class"],
            parameterType="Required",
            direction="Input")

        input2 = arcpy.Parameter(
            displayName="Unique Values Field",
            name="UniqueField",
            datatype="Field",
            parameterType="Required",
            direction="Input")

        input2.parameterDependencies = [input1.name]

        input3 = arcpy.Parameter(
            displayName="Output",
            name="output",
            datatype="GPFeatureLayer",
            parameterType="Derived",
            direction="Output")

        input3.parameterDependencies = [input2.name]
        
        params = [input1, input2, input3]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, params, messages):
    
        import arcpy
        import re

        # Get parameters
        FeatureLayer1 = params[0].valueAsText
        UniqueField = params[1].valueAsText


        # Set workspace and environment settings
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        arcpy.env.overwriteOutput = True
        arcpy.env.addOutputsToMap = True

        def sanitize_feature_class_name(name):
            # Replace spaces with underscores
            name = name.replace(" ", "_")
            # Remove special characters
            name = re.sub(r'\W+', '', name)
            return name

        try:
            # Get the first map in the current project
            map_doc = aprx.activeView.map  # Automatically selects the first map
            arcpy.AddMessage("Using first map: {0}".format(map_doc.name))
    
            # List to hold the output layers
            output_layers = []

            # Create a search cursor and loop through the selected records
            with arcpy.da.SearchCursor(FeatureLayer1, [UniqueField], "", "", "", ("DISTINCT", UniqueField)) as cursor:
            ##with arcpy.da.SearchCursor(FeatureLayer1, [UniqueField]) as cursor:  #for when you want all rows
                for i, row in enumerate(cursor):
                    UniqueString = row[0]
                    sanitized_name = sanitize_feature_class_name(str(UniqueString))
                    whereClause = "{} = '{}'".format(arcpy.AddFieldDelimiters(FeatureLayer1, UniqueField), UniqueString)
            
                    # Create a unique temporary layer name
                    tempLayerName = "tempLayer_" + sanitized_name
            
                    try:
                        # Make a feature layer of just the current selection
                        arcpy.MakeFeatureLayer_management(FeatureLayer1, tempLayerName, whereClause)
                        arcpy.AddMessage("Processing {0}.".format(UniqueString))
                
                        # Add the feature layer to the map with a meaningful name
                        result = arcpy.management.MakeFeatureLayer(tempLayerName)
                        layer = result.getOutput(0)
                        map_doc.addLayer(layer)
                
                        # Set the name of the added layer
                        added_layer = map_doc.listLayers(layer.name)[0]
                        added_layer.name = sanitized_name
                
                        output_layers.append(added_layer)
                        arcpy.AddMessage("Created and added feature layer: {0}".format(sanitized_name))
                
                    except Exception as e:
                        arcpy.AddError("Could not create feature layer for {0}. Error: {1}".format(UniqueString, e))
        except Exception as e:
            arcpy.AddError("There was a problem performing the spatial selection or creating the feature layer. Error: {0}".format(e))
        finally:
            # Clean up cursor
            del row, cursor
            arcpy.AddMessage("OUTPUT AT THIS MAP FRAME: {0}".format(map_doc.name))

        # Set the output parameter for the feature layers
        params[2].value = ";".join([layer.name for layer in output_layers])




        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return
