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

        # buffer the airspace (400 meters) to get the nodes within the airspace
        constrained_airspace = self.constrained_airspace.buffer(10)

        send_bool = self.sending_nodes['geometry'].apply(lambda x: x.within(constrained_airspace.values[0]))
        receive_bool = self.receiving_nodes['geometry'].apply(lambda x: x.within(constrained_airspace.values[0]))

        self.sending_nodes = self.sending_nodes[send_bool]
        self.receiving_nodes = self.receiving_nodes[receive_bool]

    def process(self) -> None:
        ...