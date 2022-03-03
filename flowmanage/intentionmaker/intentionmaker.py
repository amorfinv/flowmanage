import os
from multiprocessing import Pool as ThreadPool
from rich.progress import track

import osmnx as ox
import numpy as np
import pandas as pd
import geopandas as gpd

import flowmanage as fm

class IntentionMaker:
    def __init__(self) -> None:

        # read osmx graph from data
        self.G = ox.load_graphml(fm.settings.graph_path)

        # get nodes and edges
        self.nodes, self.edges = ox.graph_to_gdfs(self.G)
        
        # get receving and sending nodes
        self.receiving_nodes = gpd.read_file(fm.settings.receiving_nodes)
        self.sending_nodes = gpd.read_file(fm.settings.sending_nodes)

        # get constrained airspace
        const_path = os.path.join(fm.settings.geo_data, 'airspace', 'constrained_airspace.gpkg')
        self.constrained_airspace = gpd.read_file(const_path)

        # get more settings
        self.min_distance = fm.settings.min_distance

    def process(self) -> None:

        # preparation for intention maker

        # buffer the airspace (10 meters) to get the nodes within the constrained airspace
        self.buffer_nodes(10)

        # get valid destinations
        self.get_valid_destinations()

    def buffer_nodes(self, buff_dist=10) -> None:
        
        # buffer the airspace (400 meters) to get the nodes within the airspace
        constrained_airspace = self.constrained_airspace.buffer(buff_dist)

        send_bool = self.sending_nodes['geometry'].apply(lambda x: x.within(constrained_airspace.values[0]))
        receive_bool = self.receiving_nodes['geometry'].apply(lambda x: x.within(constrained_airspace.values[0]))

        self.sending_nodes = self.sending_nodes[send_bool]
        self.receiving_nodes = self.receiving_nodes[receive_bool]
    
    def get_valid_destinations(self) -> None:
        # TODO: vectorize this
        # get list of valid sending receiving pairs
        # get the distance between each origin and destination point
        valid_destinations = []
        for _, row in self.sending_nodes.iterrows():

            # find potential destination points when distance is greater than minimum
            potential_destinations = self.receiving_nodes.loc[
                (self.receiving_nodes["geometry"].distance(row["geometry"]) > self.min_distance)
            ].index.tolist()

            # append to a list of valid destinations for a particular origin
            valid_destinations.append(potential_destinations)

        # add the list of valid destinations to the origin gdf
        self.sending_nodes["valid_destinations"] = valid_destinations