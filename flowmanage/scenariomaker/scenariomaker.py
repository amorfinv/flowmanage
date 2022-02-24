import os
import json
import sys
from multiprocessing import Pool as ThreadPool

import osmnx as ox
import numpy as np

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
        
        # read osmx graph from data
        self.G = ox.load_graphml(fm.settings.graph_path)

        # get nodes and edges
        self.nodes, self.edges =  ox.graph_to_gdfs(self.G)

    def process(self):
        ...

    def create_scen(self, intention_file_name):
        flight_intention_list  = []
        with open(self.intention_folder + intention_file_name) as file:
            for line in file:
                line = line.strip()
                line = line.split(',')
                flight_intention_list.append(line)
        

    def Intention2Scn()-> None:
        ...
        # # Step 2: Generate traffic from the flight intention file
        # generated_traffic, loitering_edges_dict = bst.Intention2Traf(flight_intention_list, edges.copy())
        # #print('Traffic generated!')
        
        # # create a loitering edges dill
        # scenario_loitering_dill_folder = 'scenario_loitering_dills/'
        # scenario_loitering_dill_name = intention_file_name.replace('.csv','.dill')
        # output_file=open(scenario_loitering_dill_folder + scenario_loitering_dill_name, 'wb')
        # dill.dump(loitering_edges_dict,output_file)
        # output_file.close()
        # #print('Created loitering dill')
        
        # # Step 3: Loop through traffic
        # lines = []
        # for cnt, flight in enumerate(generated_traffic):
        
        #     # if cnt>10:#0 :
        #     #     break #stop at 20 aircrafts or change that
        
        #     # Step 4: Add to dictionary
            
        #     # Get the flight intention information
        #     drone_id = flight[0]
        #     aircraft_type = flight[1]
        #     start_time = flight[2]
        #     origin_lat = flight[3][1]
        #     origin_lon = flight[3][0]
        #     dest_lat = flight[4][1]
        #     dest_lon = flight[4][0]
        #     file_loc = flight[5]
        #     priority = flight[7]
        #     geoduration = flight[8]
        #     geocoords = flight[9] 
        
        #     # constants for scenario
        #     start_speed = 0.0
        #     qdr = 0.0
        #     alt = 0.0
        
        #     # Convert start_time to Bluesky format
        #     start_time = round(start_time)
        #     m, s = divmod(start_time, 60)
        #     h, m = divmod(m, 60)
        #     start_time_txt = f'{h:02d}:{m:02d}:{s:02d}>'
        
        #     # QUEUE COMMAND
        #     if geocoords:
        #         queue_text = f'QUEUEM2 {drone_id},{aircraft_type},{file_loc},{origin_lat},{origin_lon},{dest_lat},{dest_lon},{qdr},{alt},{start_speed},{priority},{geoduration},{geocoords}\n'
        #     else:
        #         queue_text = f'QUEUEM2 {drone_id},{aircraft_type},{file_loc},{origin_lat},{origin_lon},{dest_lat},{dest_lon},{qdr},{alt},{start_speed},{priority},{geoduration},\n'
            
        #     lines.append(start_time_txt + queue_text)
            
        
        # # write stuff to file
        # scenario_folder = 'scenarios/'
        # scenario_file_name = intention_file_name.replace('csv','scn')
        
        # # Step 4: Create scenario file from dictionary
        # with open(scenario_folder+scenario_file_name, 'w+') as f:
        #     # f.write('00:00:00>HOLD\n00:00:00>PAN 48.204011819028494 16.363471515762452\n00:00:00>ZOOM 10\n')
        #     f.write('00:00:00.00>FF\n')
        #     f.write('00:00:00>STARTM2LOG\n')
        #     f.write('00:00:00>ASAS ON\n00:00:00>RESO SPEEDBASEDV3\n00:00:00>CDMETHOD M2STATEBASED\n')
        #     f.write('00:00:00>STREETSENABLE\n')
        #     f.write(f'00:00:00>loadloiteringdill {scenario_loitering_dill_name}\n')
        #     f.write('00:00:00>CASMACHTHR 0\n')
        #     f.write('00:00:00>LOADGEOJSON open_geofence id height\n00:00:00>LOADGEOJSON bldg_geofence fid h\n')
        #     f.write(''.join(lines))
            
        # # print(intention_file_name)

def main():
    # create_scen(flight_intention_files[0])
    pool = ThreadPool(6)
    results = pool.map(create_scen, flight_intention_files)
    pool.close()

if __name__ == '__main__':
    main()
