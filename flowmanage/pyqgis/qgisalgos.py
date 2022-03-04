from qgis.core import QgsVectorLayer, QgsCoordinateReferenceSystem
import flowmanage as fm
import os

class QgisAlgos:

    """
    Class contains functions that will be ran if they are in the settings.cfg
    """

    def __init__(self, processing: object) -> None:

        # get processing object from Qgis
        self.processing = processing

        # get list of functions in this class
        # They will be ran if they are in the settings.cfg
        self.qgis_funcs = [
            getattr(self, func) for func in dir(self) if callable(getattr(self, func)) and not func.startswith("__")
            ]

    def create_grid(self) -> None:
        """
        Code creates a grid of points of squares.
        """

        fm.con.print('[magenta]Creating grid from constrained airspace...')

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

        self.processing.run("native:creategrid", grid_inputs)