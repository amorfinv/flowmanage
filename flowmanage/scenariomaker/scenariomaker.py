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
        self.nodes, self.edges =  ox.graph_to_gdfs(self.G)

    def process(self):

        # Loop through intention files
        for intention_file in track(self.intention_files, description="[magenta]Processing...", 
                        console=fm.con):
            
            # read the intention file
            flight_intention  = []
            file_path = os.path.join(self.intention_folder, intention_file)

            flight_intention_df = pd.read_csv(file_path, names=fm.settings.intention_cols)

            with open(file_path) as file:
                for line in file:
                    line = line.strip()
                    line = line.split(',')
                    flight_intention.append(line)
        
            # save to scenario
            self.Intention2Traf(flight_intention, intention_file)
 
    def Intention2Traf(self, flight_intention_list, intention_name) -> None:
        """Processes a flight intention list and saves it to a scenario file

        Args:
            flight_intention_list (list): [description]
        """

        ac_no = 1
        lines = []
        for flight_intention in flight_intention_list:
            
            # get acid and actype
            acid = flight_intention[0]
            actype = flight_intention[1]

            # get the starting time in seconds
            spawn_time = flight_intention[2]

            # get last two entries of aicraft type for start_speed
            start_speed = int(actype[-2:])

            # start altitude and qdr
            alt = 30
            qdr = 0

            # get the origin and destination
            round_int = 8
            origin_lon = round(float(flight_intention[3]),round_int)
            origin_lat = round(float(flight_intention[4]),round_int)

            # get the destination location
            dest_lon = round(float(flight_intention[5]),round_int)
            dest_lat = round(float(flight_intention[6]),round_int)

            # get the priority
            priority = int(flight_intention[7])
            
            cretext = f'CREM2 {acid},{actype},{origin_lat},{origin_lon},{dest_lat},{dest_lon},{qdr},{alt},{start_speed},{priority}\n'
            
            lines.append(spawn_time + '>' + cretext)

        # write stuff to file
        scenario_folder = fm.settings.scenarios
        scenario_file_name = intention_name.replace('csv','scn')

        scenario_path = os.path.join(scenario_folder, scenario_file_name)
        
        # Step 4: Create scenario file from dictionary
        with open(scenario_path, 'w+') as f:
            
            # first write the header from settings
            f.write(''.join(fm.settings.scenario_header))
            f.write(''.join(lines))
        

def main():
    # create_scen(flight_intention_files[0])
    pool = ThreadPool(6)
    results = pool.map(create_scen, flight_intention_files)
    pool.close()

if __name__ == '__main__':
    main()
