import json

import numpy as np
from copy import deepcopy

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
        self.heading_airspace = fm.settings.heading_airspace
        
        self.airspace_filepath = fm.settings.airspace_filepath

        self.heading_constrained = fm.settings.heading_constrained
        
        # Initialize the airspace config dictionary
        self.airspace_config = {}
        self.airspace_info = {}
        
    def process(self) -> None:

        # step 1.a: initialize the airspace info
        layer_heights = list(range(self.min_height, self.max_height + self.layer_spacing, self.layer_spacing))
        self.airspace_info = {'levels': layer_heights, 'spacing': self.layer_spacing}
        
        # step 1.b: create the heading airspace if desired
        if self.heading_airspace:
            height_dict, angle_dict, angle_ranges = self.build_heading_airspace(layer_heights)
            
            # extend the flight information dictionary
            self.airspace_info['headings'] = angle_ranges
            self.airspace_info['angle_spacing'] = self.angle_spacing
            
            # create a layers dictionary
            layers_heading = {'heights': height_dict, 'angle': angle_dict}
        
        # step 2 create the dictionary of layers and pattern list
        # loop through self.stack_dict keys
        for stack_name, stack_list in self.stack_dict.items():
            
            if stack_name != 'open':
                # not open airspace
                layers_levels, pattern = self.build_layer_airspace_dict(layer_heights, stack_list, 'levels')
                layers_range, pattern = self.build_layer_airspace_dict(layer_heights, stack_list, 'range')

                # here check if there is a constrained heading airspace
                if self.heading_constrained:
                    # modify the layers_levels and layers_range dictionaries
                    layers_levels = self.constrained_heading(layer_heights, layers_levels, pattern, stack_list)
                    layer_heights_ranges = [f'{x-self.layer_spacing/2}-{x+self.layer_spacing/2}' for x in layer_heights]
                    layers_range = self.constrained_heading(layer_heights_ranges, layers_range, pattern, stack_list)


                self.airspace_config[stack_name] = {'levels': layers_levels, 'range': layers_range, 'pattern': pattern}
            else:
                # open airspace (headings)
                layers_levels, pattern = self.build_heading_airspace_dict(layer_heights, stack_list, angle_ranges, 'levels')
                layers_range, pattern = self.build_heading_airspace_dict(layer_heights, stack_list, angle_ranges, 'range')

                self.airspace_config[stack_name] = {'levels': layers_levels, 'range': layers_range, 'pattern': pattern, 'heading': layers_heading}
        
        
        airspace = {'config': self.airspace_config, 'info': self.airspace_info}

        # save layers to json
        with open(self.airspace_filepath, 'w') as fp:
            json.dump(airspace, fp, indent=4)
            
        fm.con.print(f'[magenta]Saving airspace json to [bold green]{self.airspace_filepath}[/] ...')

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
        # remove any layer not in stack from self.info_layers
        info_layers = [x for x in self.info_layers if x in stack_layers]
        layer_indices = {}
        for layer in info_layers:
            layer_indices[layer] = [i for i,val in enumerate(layer_ids) if val==layer]
        
        # initialize the layer dictionary
        layer_dict = {}
        
        # if including level zero in layer dictionary
        if self.ground_level_layer:
            # initlaize the value with an empty type
            layer_dict_value = ['']

            for closest_layer in info_layers:
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
                layer_top = self.layer_output(layer_heights[extreme_layers[-1]], opt)

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
            for closest_layer in info_layers:
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

    def build_heading_airspace_dict(self, layer_heights, stack_layers, angle_ranges, opt):
        """
        .....
        Args:
            layer_heights (list): list of layer heights [30, 60, 90..., 480]
            stack_closest_layers (list): Order of layer ids to repeat for which to provide information in return dictionary.
            angle_ranges (list): list of angle ranges [0-45, 45-90, 90-135,...]
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
        # remove any layer not in stack from self.info_layers
        info_layers = [x for x in self.info_layers if x in stack_layers]
        layer_indices = {}
        for layer in info_layers:
            layer_indices[layer] = [i for i,val in enumerate(layer_ids) if val==layer]
        
        # initialize the layer dictionary
        layer_dict = {}
        
        # if including level zero in layer dictionary
        if self.ground_level_layer:
            # initlaize the value with an empty type
            layer_dict_value = ['']

            # closest bottom and top empty as there is no match
            layer_dict_value.append('')
            layer_dict_value.append('')

            if self.extreme_layer:
                extreme_layers = np.array(layer_indices[self.extreme_layer])

                layer_bottom = self.layer_output(layer_heights[extreme_layers[0]], opt)
                layer_top = self.layer_output(layer_heights[extreme_layers[-1]], opt)

                layer_dict_value.append(layer_bottom)
                layer_dict_value.append(layer_top)

            if opt == 'levels':
                layer_key = 0
            elif opt == 'range':
                layer_key = f'0-{self.layer_spacing/2}'
            
            layer_dict[layer_key] = layer_dict_value

        for idx, height in enumerate(layer_heights):
            
            # make deep copy and rename layer
            angle_ranges_tmp = deepcopy(angle_ranges)
            angle_ranges_tmp[idx] = ''
            
            # initialize the list at this level
            layer_dict_value = [layer_ids[idx]]
            
            # get angle range and matching idx
            angle_range = angle_ranges[idx]
    
            other_idx = angle_ranges_tmp.index(angle_range)
            
            if idx < other_idx:
                layer_dict_value.append('')
                layer_dict_value.append(self.layer_output(layer_heights[other_idx], opt))
            else:
                layer_dict_value.append(self.layer_output(layer_heights[other_idx], opt))
                layer_dict_value.append('')

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

    def build_heading_airspace(self, flight_levels):
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
        start_ind = self.min_angle
        end_ind = self.max_angle + self.angle_spacing

        # get list of angles
        angles = [idx for idx in range(start_ind, end_ind, self.angle_spacing)]
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
            height_dict_ranges[level] = int(angle_ranges[idx].split('-')[0]) + self.angle_spacing / 2
        
        height_dict = {'ranges': height_dict_levels, 'center': height_dict_ranges}
        
        # reverse the dictionary and keep non-unique values
        angle_dict_ranges = {v: [k for k, v2 in height_dict_levels.items() if v2 == v] for v in set(height_dict_levels.values())}

        # create another dictionary similar to one above but with center of angle range
        angle_dict_center = {}
        for k, v in angle_dict_ranges.items():
            angle_dict_center[int(k.split('-')[0]) + self.angle_spacing / 2] = v
        
        angle_dict = {'ranges': angle_dict_ranges, 'center': angle_dict_center}

        return height_dict, angle_dict, angle_ranges

    def constrained_heading(self, layer_heights, layers_levels, pattern, stack_list):
        """ This function creates a constrained heading pattern. That extends the dictionary
        created by build_layer_airspace_dict. It adds another dimmension to this dictionary.
        It looks at min_angle_constrained, max_angle_constrained, and angle_spacing_constrained.
        to subdivide the stack of layers into specific heading ranges. If it can't fit the
        heading ranges equally into the stack the layers that don't fit will be made free layers.
        For example. 
        -assume 5 heading ranges (spacing 72 degrees). 
        -asssume each heading range will get a C, T and F layer.
        -This gives a total of 15 layers.
        -However if we actually have 16 layers 30,60...480, then the last layer will be a free layer.
        Args:
            layer_heights (list): list of layer heights
            layers_levels (dictionary): layer levels dictionary from build_layer_airspace_dict
            pattern (list): layer list showing the pattern
            stack_list (list): layer stack from settings.
        Returns:
            [dictionary]: constrained heading dictionary that is similar to output
            of build_layer_airspace_dict. However, there is a new dimension for the
            heading range.

        """
        # get the angle pattern
        start_ind = fm.settings.min_angle_constrained
        end_ind = fm.settings.max_angle_constrained + fm.settings.angle_spacing_constrained

        # get list of angles
        angles = [idx for idx in range(start_ind, end_ind, fm.settings.angle_spacing_constrained)]
        
        angle_ranges = []
        
        for idx in range(len(angles) - 1):
            angle_ranges.append(f'{angles[idx]}-{angles[idx + 1]}')
        # if the number of layers is greater than angle_ranges*stack_list, then label the
        # end layers as Free layers ('F')
        if len(pattern) > len(angle_ranges) * len(stack_list):
            free_layers = len(pattern) - len(angle_ranges) * len(stack_list)

            # label the end layers as free layers
            for i in range(free_layers):
                pattern[~i] = 'F'

    
        # make a layer dict with the angle_range as key and an empty list as value
        # then fill list with the heights for each angle range
        layer_dict = {x:[] for x in angle_ranges}
        for idx, angle_range in enumerate(angle_ranges):
            # get the layer heights as multiples of stack
            selected_height_idx = list(range(idx * len(stack_list), (idx + 1) * len(stack_list)))
            
            layer_dict[angle_range] = [layer_heights[i] for i in selected_height_idx]

        # make a new dict that has the layer_levels dict for each angle range
        new_dict = {}
        for angle_range in angle_ranges:
            new_dict[angle_range] = deepcopy(layers_levels)
        # new_dict = {x:layers_levels for x in angle_ranges}

        for angle_range, levels in new_dict.items():
            # relevant layer heights
            rel_heights = layer_dict[angle_range]

            # other heights
            other_heights = [i for i in layer_heights if i not in rel_heights]
            
            min_height = min(layer_dict[angle_range])
            max_height = max(layer_dict[angle_range])

            # loop through the relevant heights
            for rel_height in rel_heights:

                # loop through the first 7 entries of levels[rel_height]
                for idx, level in enumerate(levels[rel_height][:7]):
                    if isinstance(level, str) or min_height <= level <= max_height:
                        continue
                    else:
                        # get the closest layer height
                        levels[rel_height][idx] = ""

            
            # loop through the other heights
            for other_height in other_heights:
                # first see if it is below or above the relevant heights
                if other_height < min_height:
                    # loop through the first 7 entries of levels[rel_height]
                    for idx, level in enumerate(levels[other_height][:7]):
                        
                        # make all layers free
                        if idx == 0:
                            levels[other_height][idx] = "F"
                        # even values are top
                        elif not idx%2:
                            levels[other_height][idx] = rel_heights[int(idx/2 -1)]
                        else:
                            # get the closest layer height
                            levels[other_height][idx] = ""
                
                else:
                    # values above the relevant heights
                    # loop through the first 7 entries of levels[rel_height]
                    for idx, level in enumerate(levels[other_height][:7]):
                        # make all layers free
                        if idx == 0:
                            levels[other_height][idx] = "F"
                        # odd values are bottom
                        elif idx%2:
                            levels[other_height][idx] = rel_heights[int((idx-1)/2)]
                        else:
                            # get the closest layer height
                            levels[other_height][idx] = ""


            # check the ground level
            if self.ground_level_layer:
                layer_key = list(set(layers_levels.keys()) - set(layer_heights))[0]
                # loop through the first 7 entries of levels[rel_height]
                for idx, level in enumerate(levels[layer_key][:7]):
                    # make all layers free
                    if idx == 0:
                        levels[layer_key][idx] = ""
                    # even values are top
                    elif not idx%2:
                        levels[layer_key][idx] = rel_heights[int((idx-1)/2)]
                    else:
                        # get the closest layer height
                        levels[layer_key][idx] = ""

            # create a new dict that has the layer_levels dict for each angle range
            new_dict[angle_range] = levels
        
        return new_dict
