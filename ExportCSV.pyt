# -*- coding: utf-8 -*-

import arcpy
import os
import time


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
        self.label = "Export to CSV"
        self.description = "Exports a table to a CSV file. Defaults to the DATA folder (if it exists) or the project home folder."

    def getParameterInfo(self):
        """Define the tool parameters."""

        input_table = arcpy.Parameter(
            displayName="Input Table",
            name="input_table",
            datatype=["Table", "Table View"],
            parameterType="Required",
            direction="Input"
        )

        output_folder = arcpy.Parameter(
            displayName="Output Folder",
            name="output_folder",
            datatype="Folder",
            parameterType="Optional",
            direction="Input"
        )

        output_csv = arcpy.Parameter(
            displayName="Output CSV",
            name="output_csv",
            datatype="DEFile",
            parameterType="Derived",
            direction="Output"
        )

        params = [input_table, output_folder, output_csv]
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

    def execute(self, params, messages):
        """Main tool execution."""
        input_table = params[0].valueAsText
        output_folder = params[1].valueAsText

        # Get the output CSV path
        output_csv = os.path.join(output_folder, f"{os.path.basename(input_table)}.csv")

        # Export the table
        try:
            arcpy.conversion.TableToTable(input_table, output_folder, os.path.basename(output_csv))
            arcpy.AddMessage(f"Exported {input_table} to {output_csv}")
        except Exception as e:
            arcpy.AddError(f"Failed to export table: {str(e)}")
            raise

        # Attempt to delete the .xml file
        output_csv_xml = output_csv + ".xml"

        # Wait briefly in case ArcGIS Pro is still writing the XML
        time.sleep(1)

        try:
            if os.path.isfile(output_csv_xml):
                os.remove(output_csv_xml)
                arcpy.AddMessage(f"Deleted temporary XML file: {output_csv_xml}")
        except Exception as e:
            arcpy.AddWarning(f"Could not delete XML file: {output_csv_xml}. Error: {str(e)}")

