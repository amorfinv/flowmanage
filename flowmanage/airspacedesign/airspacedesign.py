import os
import json

import osmnx as ox
import numpy as np
import pandas as pd
import geopandas as gpd
import bisect

import flowmanage as fm

class AirspaceDesign:
    def __init__(self) -> None:
        
        # process settings
        self.min_height = fm.settings.min_height
        self.max_height = fm.settings.max_height
        self.layer_spacing = fm.settings.layer_spacing

        self.min_angle = fm.settings.min_angle
        self.max_angle = fm.settings.max_angle
        self.angle_spacing = fm.settings.angle_spacing

        self.stack_dict = fm.settings.stack_dict
        self.info_layers = fm.settings.info_layers
        self.extreme_layer = fm.settings.extreme_layer
        self.ground_level_layer = fm.settings.ground_level_layer

    def process(self) -> None:

        # step 1: initialize the flight dictionary
        layer_heights = list(range(self.min_height, self.max_height + self.layer_spacing, self.layer_spacing))
        flight_dict = {'levels': layer_heights, 'spacing': self.layer_spacing}
        
        # step 2 create the dictionary of layers and pattern list
        # loop through self.stack_dict keys
        airspace_config = {}
        for stack_name, stack_list in self.stack_dict.items():
            layers_levels, pattern = self.build_layer_airspace_dict(layer_heights, stack_list, 'levels')
            layers_range, pattern = self.build_layer_airspace_dict(layer_heights, stack_list, 'range')

            airspace_config[stack_name] = {'levels': layers_levels, 'range': layers_range, 'pattern': pattern}

        fm.con.print(airspace_config)
        fm.con.print(flight_dict)

        ...

    def build_layer_airspace_dict(self, layer_heights, stack_layers, opt):
        """ This creates an airsapce layer dictionary based on the minimum height, 
        maximum height, spacing, and repeating pattern of the layers. Units can
        be anything but they must be consistent. Minimum and maximum heights are
        heights where aircraft are expected to be. The layer dictionary returned
        contains the layer level/range and information about type of layer and
        levels/ranges of surrounding aircraft. At the moment only works for layers
        that have 3 sub layers and repeat. There is also an option to include information
        about the out of bounds level in the layer dictionary.
        Args:
            layer_heights (list): list of layer heights [30, 60, 90..., 480]
            stack_closest_layers (list): Order of layer ids to repeat for which to provide information in return dictionary.
            opt (string): If 'range' return dictionary with keys contaitning range of layer heights.
                        If 'levels' return dictionary with keys containing flight levels.
        Returns:
            [dictionary]: layer dictionary containing the layer level/range as the key (string/int).
                        The value of dictionary is a list. The first entry gives the layer identifier.
                        The next entries contains info about layers surrounding the current layer. The
                        order of this information depends on closest_layers list.
                        
                        Example:
                        layers = build_layer_airspace_dict(25, 500, 25, ['C', 'T', 'F'], ['C', 'T', 'F'], 'C', 'levels')
                        one entry in the dictionary would be as follows:
                        {layer level: [layer id, {bottom 'C' layer level), (top 'C' layer level), (bottom 'T' layer level), 
                                        (top 't' layer), (bottom 'F' layer level), (top 'F' layer level), (lowest extreme layer),
                                        (highest extreme layer)]
                        }
                        If out_of_bounds is True, then the dictionary will also contain information about the layer below
                        the lowest layer.
            [list]: list of layer identifiers in order. Contains no information about the out of bounds layers.
        """    
        # get the list of layer identifiers
        n_layers = len(layer_heights)
        n_type_layers = len(stack_layers)
        layer_ids = [f'{stack_layers[idx % n_type_layers]}' for idx in range(n_layers)]
        
        # find the indices of layer choices
        layer_indices = {}
        for layer in self.info_layers:
            layer_indices[layer] = [i for i,val in enumerate(layer_ids) if val==layer]
        
        # initialize the layer dictionary
        layer_dict = {}
        
        # if including level zero in layer dictionary
        if self.ground_level_layer:
            # initlaize the value with an empty type
            layer_dict_value = ['']

            for closest_layer in self.info_layers:
                # bottom is always empty
                layer_dict_value.append('')
                idx_top = layer_indices[closest_layer][0]

                # top 
                idx_top = layer_indices[closest_layer][0]
                layer = self.layer_output(layer_heights[idx_top], opt)
                layer_dict_value.append(layer)

            if self.extreme_layer:
                extreme_layers = np.array(layer_indices[self.extreme_layer])

                layer_bottom = self.layer_output(layer_heights[extreme_layers[0]], opt)
                layer_top = self.layer_output(layer_heights[extreme_layers[1]], opt)

                layer_dict_value.append(layer_bottom)
                layer_dict_value.append(layer_top)

            if opt == 'levels':
                layer_key = 0
            elif opt == 'range':
                layer_key = f'0-{self.layer_spacing/2}'
            
            layer_dict[layer_key] = layer_dict_value

        for idx, height in enumerate(layer_heights):

            # initialize the list at this level
            layer_dict_value = [layer_ids[idx]]
            
            # get closet layers
            for closest_layer in self.info_layers:
                indices_closest_layer = np.array(layer_indices[closest_layer])
                indices_left = indices_closest_layer[indices_closest_layer < idx]
                indices_right = indices_closest_layer[indices_closest_layer > idx]

                if not len(indices_left):
                    layer_dict_value.append('')
                else:
                    layer = self.layer_output(layer_heights[indices_left[-1]], opt)
                    layer_dict_value.append(layer)

                if not len(indices_right):
                    layer_dict_value.append('')
                else:
                    layer = self.layer_output(layer_heights[indices_right[0]], opt)
                    layer_dict_value.append(layer)

            # add the extreme layers
            if self.extreme_layer:
                extreme_layers = np.array(layer_indices[self.extreme_layer])
                
                layer_bottom = self.layer_output(layer_heights[extreme_layers[0]], opt)
                layer_top = self.layer_output(layer_heights[extreme_layers[-1]], opt)
                
                layer_dict_value.append(layer_bottom)
                layer_dict_value.append(layer_top)

            # add this value to dictionary
            layer_dict_key = self.layer_output(height, opt)
            layer_dict[layer_dict_key] = layer_dict_value
        
        return layer_dict, layer_ids

    def layer_output(self, layer, opt):
        if opt == 'range':
            layer_dict_key = f'{layer - self.layer_spacing/2}-{layer + self.layer_spacing/2}'
        elif opt == 'levels':
            layer_dict_key = layer
        
        return layer_dict_key

def build_heading_airspace(flight_levels,  min_angle, max_angle, angle_spacing):
    """ This creates an airsapce layer structure. It has the the height as a key
    and the heading angle range as a value. The heading angle range is a list of two values the lowest and highest angle.
    If there are too many flight levels, then the pattern is repeated.
    Example args:
    flight_levels = [30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330, 360, 390, 420, 450, 480]
    min_angle = 0
    max_angle = 360
    angle_spacing = 45
    Example output:
    {
        '30': [0, 45],
        '60': [45, 90],
        '90': [90, 135],
        '120': [135, 180],
        '150': [180, 225],
        '180': [225, 270],
        '210': [270, 315],
        '240': [315, 360],
        '270': [0, 45],
        '300': [45, 90],
        '330': [90, 135],
        '360': [135, 180],
        '390': [180, 225],
        '420': [225, 270],
        '450': [270, 315],
        '480': [315, 360]
    }
    Args:
        flight_levels (list): List of flight levels
        min_angle (int): minimum heading angle
        max_angle (int): maximum heading angle
        angle_spacing (int): heading angle spacing
    Returns:
        height_dict (dictionary): layer dictionary where the key is the height and the value is the heading range
        angle_dict (dictionary): layer dictionary where the key is heading range and the value is a list of the heights with the range
        angle_ranges (list): list of heading angles
    """
    # get the angle pattern
    start_ind = min_angle
    end_ind = max_angle + angle_spacing

    # get list of angles
    angles = [idx for idx in range(start_ind, end_ind, angle_spacing)]
    angle_ranges = []

    for idx in range(len(angles) - 1):
        angle_ranges.append(f'{angles[idx]}-{angles[idx + 1]}')

    # check lengths of angle_ranges and flight levels
    len_flight_levels = len(flight_levels)
    len_angle_ranges = len(angle_ranges)

    # edit the angle_ranges list if the number of flight levels is greater than the number of angle ranges
    if len_flight_levels > len_angle_ranges:
        # repeat the angle ranges
        angle_ranges = angle_ranges * (len_flight_levels // len_angle_ranges)
        angle_ranges = angle_ranges + angle_ranges[:len_flight_levels % len_angle_ranges]

    # create dictionary
    height_dict_levels = {}
    height_dict_ranges = {}
    for idx, level in enumerate(flight_levels):
        height_dict_levels[level] = f'{angle_ranges[idx]}'
        height_dict_ranges[level] = int(angle_ranges[idx].split('-')[0]) + angle_spacing / 2
    
    height_dict = {'ranges': height_dict_levels, 'center': height_dict_ranges}
    
    # reverse the dictionary and keep non-unique values
    angle_dict_ranges = {v: [k for k, v2 in height_dict_levels.items() if v2 == v] for v in set(height_dict_levels.values())}

    # create another dictionary similar to one above but with center of angle range
    angle_dict_center = {}
    for k, v in angle_dict_ranges.items():
        angle_dict_center[int(k.split('-')[0]) + angle_spacing / 2] = v
    
    angle_dict = {'ranges': angle_dict_ranges, 'center': angle_dict_center}

    return height_dict, angle_dict, angle_ranges


def main():
    # Build constrained layer structure
    min_height = 30
    max_height = 480
    spacing = 30

    # Two types of layers in constrained airspace
    layers_0_range, flight_dict, pattern_0 = build_layer_airspace_dict(min_height, max_height, spacing, ['C', 'T', 'F'], ['C', 'T', 'F'], 'C', True, 'range')
    layers_0_levels, _, _ = build_layer_airspace_dict(min_height, max_height, spacing, ['C', 'T', 'F'], ['C', 'T', 'F'], 'C', True,'levels')
    
    layers_1_range, _, pattern_1 = build_layer_airspace_dict(min_height, max_height, spacing, ['F', 'T', 'C'], ['C', 'T', 'F'], 'C', True, 'range')
    layers_1_levels, _, _ = build_layer_airspace_dict(min_height, max_height, spacing, ['F', 'T', 'C'], ['C', 'T', 'F'], 'C', True, 'levels')

    # Build open layer structure
    min_angle = 0
    max_angle = 360
    angle_spacing = 45

    layers_open_range, flight_dict_hdg, pattern_open = build_layer_airspace_dict(min_height, max_height, spacing, ['C'], ['C', 'T', 'F'], 'C', True, 'range')
    layers_open_levels, _, _ = build_layer_airspace_dict(min_height, max_height, spacing, ['C'], ['C', 'T', 'F'], 'C', True, 'levels')
    height_dict, angle_dict, angle_ranges = build_heading_airspace(flight_dict_hdg['levels'], min_angle, max_angle, angle_spacing)
    layers_open_hdg = {'heights': height_dict, 'angle': angle_dict}
    
    # create layers dictionary
    layers_0 = {'range': layers_0_range, 'levels': layers_0_levels, 'pattern': pattern_0}
    layers_1 = {'range': layers_1_range, 'levels': layers_1_levels, 'pattern': pattern_1}
    layers_open = {'range': layers_open_range, 'levels': layers_open_levels, 'pattern': pattern_open, 'heading': layers_open_hdg}

    # extend the flight_dict to include heading ranges of open airspace
    flight_dict['headings'] = angle_ranges
    flight_dict['angle_spacing'] = angle_spacing

    # create overall dictionary
    airspace_config = {'0': layers_0, '1': layers_1, 'open': layers_open}
    airspace = {'config': airspace_config, 'info': flight_dict}

    # save layers to json
    with open('layers.json', 'w') as fp:
        json.dump(airspace, fp, indent=4)
