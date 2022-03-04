try:
    from qgis.core import QgsApplication, QgsVectorLayer, QgsCoordinateReferenceSystem
except ImportError:
    fm.con.print('[bold red]QGIS not found!!')
    fm.con.print('[bold red]Activate [bold magenta] [light_sea_green on grey27] qgis 🅒 ')
    exit()

import os

import flowmanage as fm

# global variable
processing = None

# Initialize qgis
def start():
    # Supply path to qgis install location
    QgsApplication.setPrefixPath(fm.settings.qgis_path, True)
    
    # import processing to make qgis algirithms available
    from processing.core.Processing import Processing

    # Initialize QGIS application with no GUI
    qgs = QgsApplication([], True)
    qgs.initQgis()

    # initialize processing algorithms and then import them as global variables
    Processing.initialize()
    global processing
    from qgis import processing 

    # run the algorithms specified in the settings
    if 'create_grid' in fm.settings.qgis_algos:
        create_grid()
            
    # exit qgis
    qgs.exitQgis()

##########################QGIS ALGORITHMS####################################

def create_grid():
    """
    Code creates a grid of points of squares.
    """

    fm.con.print('[magenta]Creating grid of from constrained airspace...')

    # get the grid size and path
    grid_size = fm.settings.grid_size
    grid_path = fm.settings.grid_path

    # get the extent of the constrained airspace
    const_path = os.path.join(fm.settings.geo_data, 'airspace', 'constrained_airspace.gpkg')
    const_airspace = QgsVectorLayer(const_path)
    extent = const_airspace.extent()

    # intialize the inputs for the algorithm and run
    grid_inputs = {'CRS' : QgsCoordinateReferenceSystem('EPSG:32633'), 
                    'EXTENT' : extent, 
                    'HOVERLAY' : 0, 
                    'HSPACING' : grid_size, 
                    'OUTPUT' : grid_path, 
                    'TYPE' : 2, 
                    'VOVERLAY' : 0, 
                    'VSPACING' : grid_size}

    processing.run("native:creategrid", grid_inputs)
