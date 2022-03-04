
import os
from multiprocessing import Pool as ThreadPool
from rich.progress import track

import osmnx as ox
import numpy as np
import pandas as pd
import geopandas as gpd

import flowmanage as fm
 
class StreetCenterPoints:
    def __init__(self) -> None:

        # read osmx graph from data
        self.G = ox.load_graphml(fm.settings.graph_path)
        ox.distance.add_edge_lengths(self.G)

        # get nodes and edges
        self.nodes, self.edges = ox.graph_to_gdfs(self.G)

    def process(self) -> None:
        
        fm.con.print('[magenta]Creating street center points...')
        
        # get all center points as gdf
        center_points = self.get_center_points(fm.settings.edge_cutoff)

        # get grid by pyqgis module
        grid = gpd.read_file(fm.settings.grid_path)
        
        # filter the points to the grid
        selected_center_points_gdf = self.filter_center_points(center_points, grid)

        # split gdf randomly into origin or destination
        selected_center_points_gdf['origin'] = np.random.choice([True, False], size=len(selected_center_points_gdf))

        # save to a file
        selected_center_points_gdf.to_file(fm.settings.center_points, driver='GPKG')
        fm.con.print('[magenta]Saving filtered center points...')

    def get_center_points(self, edge_cutoff: float) -> gpd.GeoDataFrame:
        '''
        Get all center points from the graph. Only edges longer than the edge cutoff are considered.

        Parameters
        ----------
        edge_cutoff : float
            Edge cutoff length.
        
        Returns
        -------
        gpd.GeoDataFrame
            Center points as gdf.
        '''

        # delete edges smaller than 60 meters
        edges = self.edges.loc[self.edges['length'] > edge_cutoff]

        # convert to crs 32633
        edges = edges.to_crs(epsg=32633)

        # get center poitns as gdf
        center_points = gpd.GeoSeries(edges['geometry'].apply(lambda line_geom: line_geom.interpolate(0.5, normalized=True)))

        return center_points

    def filter_center_points(self, center_points: gpd.GeoDataFrame, grid: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        '''
        Filter the center points to the grid created with create_grid. 
        Only keep one point per grid cell. It also ensures that all points are at least
        fm.settings.grid_size distance away from each other. This means that neighboring
        cells will not have a node.

        If there are many points in one cell then algorithm will keep the one
        that is furthest from the edge of the cell.

        Below is an example of how the nodes may be spread inside the grid:

        Note that there will only be points on odd rows (1,3,5,7,9...).
        For odd columns it is (1,5,9..)
        For even columns it is (3,7..)

        This will ensure that the nodes are always at least fm.settings.grid_size 
        distance from each other.

           1 2 3 4 5 6 7 8 9 10
          ---------------------
        1 |*| |*| |*| |*| |*| |
          ---------------------
        2 | | | | | | | | | | |
          ---------------------
        3 | |*| |*| |*| |*| |*|
          ---------------------
        4 | | | | | | | | | | |
          ---------------------
        5 |*| |*| |*| |*| |*| |
          ---------------------
        6 | | | | | | | | | | |
          ---------------------
        7 | |*| |*| |*| |*| |*|
          ---------------------
        8 | | | | | | | | | | |
          ---------------------
        9 |*| |*| |*| |*| |*| |
          ---------------------
       10 | | | | | | | | | | |
          ---------------------

        Parameters
        ----------
        center_points : gpd.GeoDataFrame
            Center points as gdf.
        grid : gpd.GeoDataFrame
            Grid as gdf.

        Returns
        -------
        gpd.GeoDataFrame
            Filtered center points as gdf.
        '''
        # get the entries for odd and even colums
        n_rows = grid.row.max()
        even_cols = list(range(3,n_rows + 1, 4))
        odd_cols = list(range(1,n_rows + 1, 4))

        # filter through the grid cells and get points contained in them
        selected_points = []
        for i in track(range(len(grid)), description='[magenta]Filtering center points...'):
            # get the grid cell
            cell = grid.geometry.iloc[i]

            # current row
            row_val = grid.row.iloc[i]
            col_val = grid.col.iloc[i]
            
            # TODO: A bit slow to check (row_val not in odd_cols)
            # if column is odd and the row is not in odd columns
            if (col_val % 2) and row_val not in odd_cols:
                continue
            
            # TODO: A bit slow to check (row_val not in even_cols)
            # if the column is even and the row is not in even columns
            if (not col_val % 2) and row_val not in even_cols:
                continue
            
            # get the center points within the bounding box
            center_points_in_cell = center_points.sindex.query(cell, predicate='contains')

            if len(center_points_in_cell) == 0:
                continue

            # see which point is furthest from the edges of the cell
            distances = []
            for center_point_id in center_points_in_cell:
                center_point = center_points.geometry.iloc[center_point_id]
                center_point_distance = center_point.distance(cell.boundary)
                distances.append(center_point_distance)

            # select the point with the largest distance
            selected_points.append(center_points_in_cell[np.argmax(distances)])
        
        # order the points by their value
        selected_points = np.sort(selected_points)
        
        # select the center_points with selected_points
        selected_center_points = center_points.iloc[selected_points]

        return gpd.GeoDataFrame(selected_center_points, geometry='geometry')