
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
        center_points = self.get_center_points()

        # save to a file
        center_points.to_file(fm.settings.center_points, driver='GPKG')

    def get_center_points(self) -> gpd.GeoDataFrame:

        # delete edges smaller than 60 meters
        edges = self.edges.loc[self.edges['length'] > fm.settings.edge_cutoff]

        # convert to crs 32633
        edges = edges.to_crs(epsg=32633)

        # get center poitns as gdf
        center_points = gpd.GeoDataFrame(edges['geometry'].apply(lambda line_geom: line_geom.interpolate(0.5, normalized=True)))

        # add id to center_points
        center_points['id'] = range(len(center_points))

        # convert back to 4326
        return center_points.to_crs(epsg=4326)

