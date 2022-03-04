from qgis.core import QgsVectorLayer, QgsCoordinateReferenceSystem, QgsField
from qgis.core.additions.edit import edit
from PyQt5.QtCore import QVariant
import flowmanage as fm
import os
import numpy as np

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

        grid = QgsVectorLayer(grid_path)

        # get extent of the grid
        grid_extent = grid.extent()

        # get the number of rows and columns of grid
        num_rows = int((grid_extent.height()) / grid_size)
        num_cols = int((grid_extent.width()) / grid_size)

        # TODO: combine all the for loops into one
        
        selected_fid = []
        # Get the first feature id from the layer
        for feature in grid.getFeatures():
            selected_fid.append(feature.id())
        
        # make a new list that has the grid matrix row
        row_val = []
        col_val = []

        row_count = 1
        col_count = 1
        for _ in selected_fid:
            row_val.append(row_count)
            col_val.append(col_count)

            # always increase the row count
            row_count += 1

            # if the row count is equal to the number of rows, 
            # reset the row count and increase the column count
            if row_count == num_rows + 1:
                row_count = 1
                col_count += 1
        
        # start editing qgis layer
        grid.startEditing()

        # add attribute to qgis layer
        grid.dataProvider().addAttributes([QgsField('row', QVariant.Int), QgsField('col', QVariant.Int)])
        grid.updateFields()
        
        row_col = grid.fields().indexFromName('row')
        col_col = grid.fields().indexFromName('col')
        # add the row and column values to the grid
        for i in range(len(selected_fid)):
            grid.changeAttributeValue(selected_fid[i], row_col, row_val[i])
            grid.changeAttributeValue(selected_fid[i], col_col, col_val[i])
        
        # save the grid
        grid.commitChanges()