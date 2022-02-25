import os
import json
import sys
from multiprocessing import Pool as ThreadPool
from rich.progress import track
from rich.progress import Progress

import osmnx as ox
import numpy as np
import pandas as pd

import flowmanage as fm

class ScenarioMaker:
    def __init__(self) -> None:

        # get the flight intention files to make scenarios
        self.intention_folder = fm.settings.intentions
        self.intention_files = os.listdir(fm.settings.intentions)

        if not self.intention_files:
            fm.con.print('[red bold]No intention files found!')
            fm.con.print("[red bold]Try:[/] [green]python FlowManage.py --intention")
            quit()
        # remove any hidden files
        self.intention_files = [file for file in self.intention_files if not file.startswith('.')]

        # read osmx graph from data
        self.G = ox.load_graphml(fm.settings.graph_path)

        # get nodes and edges
        self.nodes, self.edges = ox.graph_to_gdfs(self.G)

    def process(self, multi: int | None = None) -> None:

        if multi:
                pool = ThreadPool(6)
                pool.map(self.create_scen, self.intention_files)
                pool.close()
        else:
            # Loop through intention files
            for intention_file in track(self.intention_files, description="[magenta]Processing...", 
                            console=fm.con):

                # create the scenario file
                self.create_scen(intention_file)

    def create_scen(self, intention_file: str) -> None:

        # read the intention file
        file_path = os.path.join(self.intention_folder, intention_file)

        # create the dataframe
        scen_df = pd.read_csv(file_path, names=fm.settings.intention_cols)
        
        # see if any columns are missing from intention file
        missing_cols = list(set(fm.settings.scen_cols) - set(fm.settings.intention_cols))

        # add them to the dataframe
        if missing_cols:
            for col in missing_cols:
                    scen_df[col] = fm.settings.default_values[col]

        # create a column with spawn time + crecmd
        scen_df['crecmd'] = scen_df['spawn_time'] + '>' + scen_df['crecmd']

        # remove spawn time column
        scen_df.drop('spawn_time', axis=1, inplace=True)

        # save as df to csv
        scenario_folder = fm.settings.scenarios
        scenario_file_name = intention_file.replace('csv','scn')

        scenario_path = os.path.join(scenario_folder, scenario_file_name)
        scen_df.to_csv(scenario_path, index=False, header=False, columns=fm.settings.scen_cols)

        # add the header to the file
        with open(scenario_path, 'r+') as f:
            content = f.read()
            f.seek(0, 0)
            f.write(''.join(fm.settings.scenario_header) + content)
