import os

import flowmanage as fm

# Import QGIS
try:
    from qgis.core import QgsApplication, QgsVectorLayer, QgsCoordinateReferenceSystem
    # Supply path to qgis install location
    QgsApplication.setPrefixPath(fm.settings.qgis_path, True)
    from processing.core.Processing import Processing

except ImportError:
    fm.con.print('[bold red]QGIS not found!!')
    fm.con.print('[bold red]Activate [bold magenta] [light_sea_green on grey27] qgis 🅒 ')
    exit()

##########################QGIS ALGORITHMS####################################

def create_grid():
    """
    Code creates a grid of points of squares
    """

    fm.con.print('[magenta]Creating grid of from constrained airspace...')

    # get the grid size
    grid_size = fm.settings.grid_size
    const_path = os.path.join(fm.settings.geo_data, 'airspace', 'constrained_airspace.gpkg')
    const_airspace = QgsVectorLayer(const_path)

    # Now create the grid
    grid_path = fm.settings.grid_path

    grid_inputs = {'CRS' : QgsCoordinateReferenceSystem('EPSG:32633'), 
                    'EXTENT' : '596540.465300000,606393.683900000,5335138.924700000,5345123.448600000 [EPSG:32633]', 
                    'HOVERLAY' : 0, 
                    'HSPACING' : grid_size, 
                    'OUTPUT' : grid_path, 
                    'TYPE' : 2, 
                    'VOVERLAY' : 0, 
                    'VSPACING' : grid_size}

    processing.run("native:creategrid", grid_inputs)


##########################QGIS INITIALIZE####################################

# Initialize QGIS application with no GUI
qgs = QgsApplication([], True)
qgs.initQgis()

# initialize processing algorithms and then import
Processing.initialize()
from qgis import processing 


# run the algorithms
if 'create_grid' in fm.settings.qgis_algos:
    create_grid()
        
# exit qgis
qgs.exitQgis()
