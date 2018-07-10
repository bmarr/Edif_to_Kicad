#!/usr/bin/env python
""" Objects and methods for outputing KiCAD files """

import math
import numpy as np

#from kicad_common import *

def convert_kicad_coor(edif_pt):
    """ KiCAD LIB coordinates are 10 times EDIF """
    scale = 10
    return [edif_pt[0] * scale, +edif_pt[1] * scale]

class KicadArc(object):
    """ Convert EDIF 2 point arc to KiCAD 3 point arc """
    def __init__(self):
        self.def_field = {'XY_center':{0, 0},
                          'radius':0,
                          'angle1':0,
                          'angle2':0,
                          'unit':0,
                          'convert':1,
                          'width':0,
                          'fill':'N',
                          'XY_arcpoints':[],
                         }
        self.arcpoints = []
        self.offset = [0, 0]

    def add_point(self, xpos, ypos):
        """ Add a point (1 of 3) """
        self.arcpoints.append([xpos, ypos])

    def set_offset(self, xpos, ypos):
        """ Apply an offset to the shape (ie. power ports) """
        self.offset = [xpos, ypos]

# https://stackoverflow.com/questions/20314306/find-arc-circle-equation-given-three-points-in-space-3d
    def output(self):
        """ Write the shape as Kicad library strings """
        xpos, ypos = self.arcpoints[2]
        startxy = np.array([xpos, ypos])        # start point
        xpos, ypos = self.arcpoints[1]
        pointxy = np.array([xpos, ypos])        # a point on the curve
        xpos, ypos = self.arcpoints[0]
        endxy = np.array([xpos, ypos])        # end point

        a_norm = np.linalg.norm(endxy - pointxy)
        b_norm = np.linalg.norm(endxy - startxy)
        c_norm = np.linalg.norm(pointxy - startxy)
        """
        s_factor = (a_norm + b_norm + c_norm) / 2
        radius = a_norm * b_norm * c_norm / 4
                  / np.sqrt(s_factor * (s_factor - a_norm)
                                        * (s_factor - b_norm)
                                        * (s_factor - c_norm))
        """
        b_factor1 = a_norm * a_norm * (b_norm * b_norm
                                       + c_norm * c_norm
                                       - a_norm * a_norm)
        b_factor2 = b_norm * b_norm * (a_norm * a_norm
                                       + c_norm * c_norm
                                       - b_norm * b_norm)
        b_factor3 = c_norm * c_norm * (a_norm * a_norm
                                       + b_norm * b_norm
                                       - c_norm * c_norm)
        centerxy = np.column_stack((startxy,
                                    pointxy,
                                    endxy)).dot(np.hstack((b_factor1,
                                                           b_factor2,
                                                           b_factor3)))
        centerxy /= b_factor1 + b_factor2 + b_factor3            # arc center

        self.def_field['XY_center'] = (centerxy)
        self.def_field['XY_arcpoints'].append(startxy) # start point
        self.def_field['XY_arcpoints'].append(endxy) # end point

        to_write = 'A '
        xpos, ypos = self.def_field['XY_center']

        to_write += str(int(xpos)) + ' ' + str(int(ypos)) + ' '
        to_write += str(self.def_field['radius']) + ' '
        to_write += str(self.def_field['angle1']) + ' '
        to_write += str(self.def_field['angle2']) + ' '
        to_write += str(self.def_field['unit']) + ' '
        to_write += str(self.def_field['convert']) + ' '
        to_write += str(self.def_field['width']) + ' '
        to_write += str(self.def_field['fill']) + ' '
        for xpos, ypos in self.def_field['XY_arcpoints']:
            to_write += str(self.offset[0] + xpos) + ' ' \
                     + str(self.offset[1] + ypos) + ' '
        to_write += '\n'
        return to_write

class KicadPoly(object):
    """ Convert EDIF poly lines to KiCAD poly lines """
    def __init__(self):
        self.def_field = {'count':0,
                          'part':0,
                          'dmg':1,
                          'pen':10,
                          'XY_poly':[],
                          'fill':'N'
                         }
        self.offset = [0, 0]

    def add_segment(self, xpos, ypos):
        """ Add a point of a line segment """
        self.def_field['XY_poly'].append([xpos, ypos])
        self.def_field['count'] += 1

    def set_offset(self, xpos, ypos):
        """ Apply an offset to the shape (ie. power ports) """
        self.offset = [xpos, ypos]

    def output(self):
        """ Write the shape as Kicad library strings """
        to_write = 'P '
        to_write += str(self.def_field['count'])+' '
        to_write += str(self.def_field['part'])+' '
        to_write += str(self.def_field['dmg'])+' '
        to_write += str(self.def_field['pen'])+' '
        for xpos, ypos in self.def_field['XY_poly']:
            to_write += str(self.offset[0] + xpos) + ' ' \
                      + str(self.offset[1] + ypos) + ' '
        to_write += str(self.def_field['fill'])
        to_write += '\n'
        return to_write


class KicadRectangle(object):
    """ Convert EDIF rectangle to KiCAD rectangle """
    def __init__(self, xpos1, ypos1, xpos2, ypos2):
        self.def_field = {'x1':xpos1, 'y1':ypos1, 'x2':xpos2, 'y2':ypos2,
                          'part':0,
                          'dmg':1,
                          'pen':10,
                          'fill':'N'
                         }
        self.offset = [0, 0]

    def set_offset(self, xpos, ypos):
        """ Apply an offset to the shape (ie. power ports) """
        self.offset = [xpos, ypos]

    def output(self):
        """ Write the shape as Kicad library strings """
        to_write = 'S '
        """
        print self.def_field
        for key in self.def_field:
            print key,"=", self.def_field[key]
        """
        to_write += str(self.offset[0] + self.def_field['x1'])+' '
        to_write += str(self.offset[1] + self.def_field['y1'])+' '
        to_write += str(self.offset[0] + self.def_field['x2'])+' '
        to_write += str(self.offset[1] + self.def_field['y2'])+' '
        to_write += str(self.def_field['part'])+' '
        to_write += str(self.def_field['dmg'])+' '
        to_write += str(self.def_field['pen'])+' '
        to_write += self.def_field['fill']+'\n'
        return to_write

class KicadCircle(object):
    """ Convert EDIF Circle to KiCAD circle """
    def __init__(self, xpos1, ypos1, xpos2, ypos2):
        distx = (xpos1-xpos2)
        disty = (ypos1-ypos2)
        radius = int(math.sqrt(distx * distx + disty * disty) / 2)
        xpos = xpos1 - distx/2
        ypos = ypos1 - disty/2
        self.def_field = {'x':xpos, 'y':ypos, 'radius':radius,
                          'part':0,
                          'dmg':1,
                          'pen':10,
                          'fill':'N'
                         }
        self.offset = [0, 0]

    def set_offset(self, xpos, ypos):
        """ Apply an offset to the shape (ie. power ports) """
        self.offset = [xpos, ypos]

    def output(self):
        """ Write the shape as Kicad library strings """
        to_write = 'C '
        """
        print self.def_field
        for key in self.def_field:
            print key,"=", self.def_field[key]
        """
        to_write += str(self.offset[0] + self.def_field['x'])+' '
        to_write += str(self.offset[1] + self.def_field['y'])+' '
        to_write += str(self.def_field['radius'])+' '
        to_write += str(self.def_field['part'])+' '
        to_write += str(self.def_field['dmg'])+' '
        to_write += str(self.def_field['pen'])+' '
        to_write += self.def_field['fill']+'\n'
        return to_write

class KicadConnection(object):
    """ Convert EDIF pin connections to KiCAD pin connections """

    def __init__(self, pin_number, pin_name=''):
        if pin_number == '':
            pin_number = pin_name
            pin_name = '~'
        #elif (pin_name==''):
        #   pin_name = '~'

        self.def_field = {'name':pin_name,
                          'pin_number': pin_number,
                          'x':0,
                          'y':0,
                          'length':0,
                          'direction':'',
                          'size_num':40,
                          'size_name':40,
                          'part':0,
                          'dmg':1,
                          'type':1,
                          'shape':'P'}
        self.offset = [0, 0]
        self.convert = 1
        self.part = 1
        self.shape = "" # line (None default)
        self.etype = "P" # passive
        #print "pin #" + str(pin_number) + ", name = " + str(pin_name)
    def set_offset(self, xpos=0, ypos=0):
        """ Apply an offset to the shape (ie. power ports) """
        self.offset = [xpos, ypos]

    def set_convert(self, connection_conv):
        """ Set the conversion of the shape """
        self.convert = connection_conv

    def set_part(self, connection_part):
        """ Set the part of the multi-part shape """
        self.part = connection_part

    def set_shape(self, connection_shape):
        """ Set the shape of the connection (rectangle, circle, ...) """
        self.shape = connection_shape

    def set_electrical_type(self, connection_etype):
        """ Set the type of the connection (passive, etc.) """
        self.etype = connection_etype

    def set_pin(self, xpos1, ypos1, xpos2, ypos2):
        """ Set the pin position """

        distx = xpos1-xpos2
        disty = ypos1-ypos2

        if distx < 0 and disty == 0:
            self.def_field['direction'] = 'R'
        if distx > 0 and disty == 0:
            self.def_field['direction'] = 'L'

        if distx == 0 and disty > 0:
            self.def_field['direction'] = 'D'
        if distx == 0 and disty < 0:
            self.def_field['direction'] = 'U'

        self.def_field['length'] = int(math.sqrt(distx * distx
                                                 + disty * disty))
        self.def_field['x'] = self.offset[0] + xpos1
        self.def_field['y'] = self.offset[1] + ypos1

    def output(self):
        """ Write the connection as Kicad library strings """
        to_write = 'X '
        to_write += str(self.def_field['name'])+' '
        to_write += str(self.def_field['pin_number'])+' '
        to_write += str(self.def_field['x'])+' '
        to_write += str(self.def_field['y'])+' '
        to_write += str(self.def_field['length'])+' '
        to_write += self.def_field['direction']+' '
        to_write += str(self.def_field['size_num'])+' '
        to_write += str(self.def_field['size_name'])+' '
        #to_write += str(self.def_field['part'])+' '
        to_write += str(self.def_field['dmg'])+' '
        to_write += str(self.def_field['type'])+' '
        to_write += self.def_field['shape']
        to_write += '\n'
        return to_write







class KicadLibraryComponent(object):
    """ Create the KiCAD library file component strings """
    _F_KEYS = ['id', 'ref', 'posx', 'posy', 'size',
               'text_orientation', 'visible', 'text_align', 'props']

    def __init__(self, name):
        self.name = name
        self.fields = []
        self.draws = []
        self.connections = []
        self.alias = ''
        self.ref = ''
        self.powerobject = 'N'
        self.pin_names_visible = 'Y'
        self.pin_numbers_visible = 'Y'
        print " new component : ", self.name


    def set_designator(self, ref):
        """ Set the reference designator """
        self.ref = ref

    def set_powerobject(self, boolean):
        """ Set to True for a power object """
        if boolean == True:
            self.powerobject = 'P'

    def set_pin_names_visible(self, boolean):
        """ Set to True to show pin names """
        if boolean == False:
            self.pin_names_visible = 'N'

    def set_pin_numbers_visible(self, boolean):
        """ Set to True to show pin numbes """
        if boolean == False:
            self.pin_numbers_visible = 'N'

    def add_field(self, field_data):
        """ Add a component field (ie. designator, footprint, parameters...) """
        def_field = {'id':None,
                     'ref':None,
                     'posx':'0',
                     'posy':'0',
                     'size':'50',
                     'text_orientation':'H',
                     'visible':'V',
                     'text_align':'L',
                     'props':'CNN'
                    }

        field = dict(list(def_field.items()) + list(field_data.items()))
        #field['id'] = str(len(self.fields))

        self.fields.append(field)
        return field

    def add_draw(self, draw):
        """ Add a shape object (ie. KicadArc, KicadPoly, etc.) """
        self.draws.append(draw)

    def add_connection(self, connection):
        """ Add an electrical connection """
        self.connections.append(connection)

    def add_alias(self, alias):
        """ Add a component alias """
        if  alias != self.name:
            self.alias = alias


    def output(self):
        """ Write the component as Kicad library strings """

        to_write = []


        try:
            test_field = self.fields[0]['id']
        except IndexError:
            test_field = None


        if test_field == None or test_field != 0:
            # missing fields
            return to_write



        to_write += ['#\n# '+self.name+'\n#\n']
        to_write += ['DEF '+
                     self.name+' '+
                     self.ref+' '+
                     '0 '+ # 0
                     '1 '+ # off
                     self.pin_numbers_visible + ' '+
                     self.pin_names_visible + ' '+
                     '1 '+
                     'F '+
                     self.powerobject + '\n'
                    ]

        to_write += ['$FPLIST\n']
        to_write += ['$ENDFPLIST\n']

        for field in self.fields:
            line = 'F'
            for key in self._F_KEYS:
                line += str(field[key]) + ' '
            to_write += [line.rstrip() + '\n']

        if self.alias != '':
            to_write += ['ALIAS '+self.alias+'\n']

        to_write += ['DRAW\n']

        for draw in self.draws:
            #print "==================>",draw.output()
            to_write += [draw.output()]

        for connection in self.connections:
            to_write += [connection.output()]

        to_write += ['ENDDRAW\n']

        to_write += ['ENDDEF\n']



        return to_write


class KicadLibrary(object):
    """ Manage a KiCAD library file """

    def __init__(self, lib_name):
        self.name = lib_name
        self.__component_list = {}


    def add_component(self, lib_component):
        """ Add a Kicad_Component to the library """
        comp_name = lib_component.name
        try:
            comp = self.__component_list[comp_name]
        except KeyError:
            self.__component_list[comp_name] = lib_component


    def output(self):
        """ Write all components to the libaray """
        #pprint.pprint(self.__component_list)
        to_write = []
        for key in self.__component_list:
            to_write += self.__component_list[key].output()
        return to_write

    def save(self, filename=None):
        """ Save the library to a library file """

        if not filename:
            filename = self.name+".lib"

        to_write = []

        to_write += "EESchema-LIBRARY Version 2.3\n#encoding utf-8\n"

        to_write += self.output()

        to_write += "#\n#End Library\n"

        library_file = open(filename, 'w')
        library_file.writelines(to_write)
        library_file.close()
