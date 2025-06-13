from qgis.PyQt.QtWidgets import QAction, QFileDialog
from qgis.gui import QgisInterface
from qgis.core import QgsVectorLayer, QgsProject
from qgis.PyQt.QtGui import QIcon
import os, glob

class BatchCSVWKTImporter:
    def __init__(self, iface: QgisInterface):
        # super().__init__()
        self.iface = iface
        # Initialize the plugin's action with an icon
        icon_path = os.path.join(os.path.dirname(__file__), 'icon.png')
        self.action = QAction(QIcon(icon_path), "CSV files importer", self.iface.mainWindow())
        self.action.triggered.connect(self.csv_importer)

    def initGui(self):
        # Add menu item and toolbar icon
        self.iface.addPluginToMenu("&My CSV Importer", self.action)
        self.iface.addToolBarIcon(self.action)

    def unload(self):
        # Remove the menu item
        self.iface.removePluginMenu("&My CSV Importer", self.action)
        self.iface.removeToolBarIcon(self.action)
        
    def csv_importer(self):
        # Get the QGIS project's parent folder
        project_path = QgsProject.instance().fileName()
        if not project_path:
            print("The QGIS project must be saved first!")
            return
        project_folder = os.path.dirname(project_path)
        parent_folder = os.path.dirname(project_folder)

        # Define the specific subfolder "_out_results_wkt" inside the parent folder
        target_folder = os.path.join(parent_folder, "_out_results_wkt")

        # Check if the target folder exists
        if not os.path.exists(target_folder):
            print(f"The folder '_out_results_wkt' does not exist in {parent_folder}!")
            return

        # Open the file selection dialog
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setDirectory(target_folder)
        file_dialog.setNameFilter("CSV files (*.csv)")
        file_dialog.setWindowTitle("Select CSV Files to Import")
        
        if file_dialog.exec_(): 
            selected_files = file_dialog.selectedFiles()
        
            # Get the CRS of the QGIS project
            project_crs = QgsProject.instance().crs().authid()
        
            for fname in selected_files:
                # Initialize data type detection
                field_types = {}
            
                with open(fname, 'r', encoding='utf-8') as file:
                    # Read header
                    header_line = file.readline().strip()
                    
                    # Fix header: Preserve WKT and properly split other columns
                    # Replace ONLY the first occurrence of `)",` with `)|` to protect WKT integrity
                    header_fixed = header_line.replace(')",', ')|', 1)
                    # Now safely split the header using `|`
                    header = header_fixed.split('|')
                    # Ensure that all WKT elements retain `)` where needed
                    header = [col + (')' if i < len(header) - 1 else '') for i, col in enumerate(header)]

                    # Initialize storage for column data
                    column_data = {column_name: [] for column_name in header}
                   
                    for line in file:
                        line_fixed = line.strip().replace(')",', ')|', 1)  # Apply the same fix to each row
                        values = line_fixed.split('|') 
        
                        if len(values) == len(header):  # Ensure correct alignment
                            for i, value in enumerate(values):
                                column_name = header[i]
                                column_data[column_name].append(value)
                        else:
                            print(f"Skipping row in {fname}: Column count mismatch")


                    # Analyze column data
                    for column_name, data in column_data.items():
                        if column_name == "WKT":
                            field_types[column_name] = "geometry"  # WKT column is geometry
                        elif all(value.strip() == "" for value in data):  # Empty column defaults to integer
                            field_types[column_name] = "integer"
                        elif any(char.isalpha() for value in data for char in value):  # If alphabetic characters exist
                            field_types[column_name] = "string"
                        else:
                            field_types[column_name] = "integer"

            print(f"Detected field types for {fname}: {field_types}")

            # Ensure QGIS properly recognizes the WKT column as geometry
            uri = f"file:///{fname}?delimiter=,&quote=\"&wktField=WKT&crs={project_crs}"
            layer_name = os.path.basename(fname).replace('.csv', '')
            layer = QgsVectorLayer(uri, layer_name, 'delimitedtext')
            
            if layer.isValid():
                QgsProject.instance().addMapLayer(layer)
            else:
                print(f"Failed to load {layer_name}")

def classFactory(iface: QgisInterface):
    return BatchCSVWKTImporter(iface)
