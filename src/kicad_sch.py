#!/usr/bin/env python
""" KiCAD schematic file generator functions and classes """

import math
import time

from kicad_common import decode_special_char, remove_quote

def convert_kicad_coor(edif_pt):
    """ KiCAD schematic coordinates are 10 times EDIF
        Y axis is flipped
    """
    scale = 10
    return [edif_pt[0] * scale, -edif_pt[1] * scale]

# TODO: add text orientation field as well?
def convert_kicad_local_coor(edif_pt, localorigin, orientation):
    """ Do text rotations relative to a point on the component
    (text is rotated and aligned relative to the component)
    """
    scale = 10
    xpos = 0
    ypos = 0
    if orientation == "R0":
        xpos = edif_pt[0]*scale # Oscale
        ypos = -edif_pt[1]*scale + 2*(localorigin[1] - -edif_pt[1]*scale) # OK
    elif orientation == "R180":
        xpos = edif_pt[0]*scale - 2*(localorigin[0] - edif_pt[0]*scale) # OK
        ypos = localorigin[1] - 2*(localorigin[1] - -edif_pt[1]*scale) # OK
    elif orientation == "MY":
        xpos = edif_pt[0]*scale + 2*(localorigin[0] - edif_pt[0]*scale) # OK
        ypos = -edif_pt[1]*scale + 2*(localorigin[1] - -edif_pt[1]*scale) # OK
    elif orientation == "MX":
        xpos = edif_pt[0]*scale # OK
        ypos = -edif_pt[1]*scale # OK
    elif orientation == "R90":
        xpos = localorigin[0] + (localorigin[1] - -edif_pt[1]*scale) # OK
        ypos = localorigin[1] + (localorigin[0] - edif_pt[0]*scale) # OK
    elif orientation == "R270":
        xpos = localorigin[0] - (localorigin[1] - -edif_pt[1]*scale) # OK
        ypos = localorigin[1] - (localorigin[0] - edif_pt[0]*scale) # OK
    elif orientation == "MYR90":
        xpos, ypos = convert_kicad_local_coor(edif_pt, localorigin, "R270") #OK
        ypos = localorigin[1] + (localorigin[0] - edif_pt[0]*scale) # OK
    elif orientation == "MXR90":
        xpos, ypos = convert_kicad_local_coor(edif_pt, localorigin, "R90") #OK
        ypos = localorigin[1] - (localorigin[0] - edif_pt[0]*scale) # OK

    return [xpos, ypos]

def convert_edif_orientation_to_hv(prop_orientation, shape_orientation):
    """ Determine the text orientation, H or V, from shape and
        property text orientation
    """
    orientation = "H"
    horizontal_set = {'R0', 'R180', 'MY', 'MX'}
    vertical_set = {'R90', 'R270', 'MYR90', 'MXR90'}

    if prop_orientation in vertical_set \
        and shape_orientation in vertical_set:
        orientation = "H"
    elif prop_orientation in horizontal_set \
        and shape_orientation in vertical_set:
        orientation = "V"
    elif prop_orientation in vertical_set \
        and shape_orientation in horizontal_set:
        orientation = "V"
    return orientation

class RotMat(object):
    """ Set up the rotation matrix for the component """
    _mat = []

    def __init__(self):
        names = []
        values = []
        for index in range(0, 4):
            rotdeg = str(90 * (index))

            rot_radians = (index + 1) * math.pi / 2
            cos_a = int(math.cos(rot_radians))
            sin_a = int(math.sin(rot_radians))

            names.append('R' + rotdeg)
            values.append([sin_a, cos_a, cos_a, -sin_a])

            if rotdeg == '0':
                names.append('MY')
                values.append([-sin_a, -cos_a, cos_a, -sin_a])
            else:
                names.append('MYR' + rotdeg)
                values.append([sin_a, cos_a, -cos_a, sin_a])

            if rotdeg == '0':
                names.append('MX')
                values.append([sin_a, cos_a, -cos_a, sin_a])
            else:
                names.append('MXR' + rotdeg)
                values.append([-sin_a, -cos_a, cos_a, -sin_a])


        self._mat = dict(zip(names, values))
        #print self._mat

    def get_matrice(self, orientation):
        """ Get a rotation matrix for a given orientation """
        try:
            ret = self._mat[orientation]
        except KeyError:
            print "*** ERROR unkwnon orientation '", orientation, "'"
            ret = None
        return ret

    def str_matrice(self, orientation):
        """ Get a KiCad formatted rotation matrix for a given orientation """
        try:
            ret = " ".join(str(coef) for coef in self._mat[orientation])
        except KeyError:
            print "*** ERROR unkwnon orientation '", orientation, "'"
            ret = None
        return ret

    def debug(self):
        """ Print a debug message """
        for index in self._mat:
            print index, ":", self._mat[index]





class KicadWire(object):
    """ Draw a wire to the schematic """
    def __init__(self, xpos1, ypos1, xpos2, ypos2):
        self._wire = [xpos1, ypos1, xpos2, ypos2]

    def output(self):
        """ Write the wire as KiCad schematic strings """
        to_write = "Wire Wire Line\n\t"
        to_write += " ".join(str(coor) for coor in self._wire)
        to_write += "\n"
        return [to_write]

# Text Label 7450 2650 0    60   ~ 0
# "test_label"
class KicadNetAlias(object):
    """ Apply a net alias """
    def __init__(self, xpos, ypos, text):
        self._pt = [xpos, ypos]
        self.text = text

    def output(self):
        """ Write a net alias as KiCad schematic strings """
        to_write = "Text Label "
        to_write += " ".join(str(coor) for coor in self._pt)
        to_write += " 0"
        to_write += " 60" # size
        to_write += " ~"
        to_write += " 0\n"
        text = remove_quote(self.text)
        text = text.replace("\\\"", "\"")
        to_write += text
        to_write += "\n"
        return [to_write]

# NoConn ~ 2900 1300
class KicadNoConnection(object):
    """ Apply a no-connect ( "X" ) to a pin """

    def __init__(self, xpos, ypos):
        self._pt = [xpos, ypos]

    def output(self):
        """ Write the no-connect as KiCad schematic strings """
        to_write = "NoConn ~ "
        to_write += " ".join(str(coor) for coor in self._pt)
        to_write += "\n"
        return [to_write]

class KicadJunction(object):
    """ Apply a junction """

    def __init__(self, xpos, ypos):
        self._pt = [xpos, ypos]

    def output(self):
        """ Write the junction as KiCad schematic strings """
        to_write = "Connection ~ "
        to_write += " ".join(str(coor) for coor in self._pt)
        to_write += "\n"
        return [to_write]

# annotate
class KicadTextNote(object):
    """ Place a text note on the schematic """
    def __init__(self, xpos, ypos):
        self._pt = [xpos, ypos]
        self.italic = False
        self.bold = False
        self.size = 60
        self.rotation = 0
        self.text = ""

    def set_text(self, text):
        """ Sets the text string of the KiCad text note """
        self.text = decode_special_char(text)

    def set_size(self, size):
        """ Sets the text size in KiCad units """
        self.size = int(size)

    def set_italic(self):
        """ Enables italic for the text string """
        self.italic = True

    def set_bold(self):
        """ Enables bold for the text string """
        self.bold = True

    def set_direction(self, rotation):
        """ Sets direction of text
            takes H or V as a parameter
        """
        self.rotation = rotation

    def output(self):
        """ Write the text note as KiCad schematic strings """
        to_write = "Text Notes "
        to_write += " ".join(str(coor) for coor in self._pt)
        to_write += " " + str(self.rotation)
        to_write += " " + str(self.size) # size
        if self.italic:
            to_write += " italic"
        else:
            to_write += " ~"
        if self.bold:
            to_write += " 12\n"
        else:
            to_write += " 0\n"
        text = remove_quote(self.text)
        text = text.replace("\\\"", "\"")
        to_write += text
        to_write += "\n"
        return [to_write]


class KicadTextPort(object):
    """ Convert EDIF port to KiCad global/offpage port """

    def __init__(self, name, xpos, ypos):
        self.name = name
        self._pt = [xpos, ypos]
        self.port_type = "UnSpc"
        self.rotation = "2"
        self.text = ""

    def set_text(self, text):
        """ Sets the text string of the port """
        self.text = decode_special_char(text)

    def set_type(self, port_type):
        """ Sets the KiCad port type
        """
        self.port_type = port_type

    def set_rotation(self, rotation):
        """ Sets the KiCad rotation of the
            global/offpage port text
             Takes comb angle, [a, b] as parameter:
            "R0":[0, 2],
			"R90":[3, 1],
			"R180":[2, 0],
			"R270":[1, 3],
			"MY":[2, 0],
			"MYR90":[1, 3],
			"MX":[0, 2],
			"MXR90":[3, 1]
        """
        self.rotation = rotation

        # pylint: disable=W0105
        """
        key_rot_def = {'R':0, 'U':1, 'L':2, 'D':3}
        try:
            self.rotation = key_rot_def[rot]
        except KeyError :
            pass
        """

    def output(self):
        """ Write the port as KiCad schematic strings """
        to_write = "Text GLabel "
        to_write += " ".join(str(coor) for coor in self._pt)
        to_write += " " + str(self.rotation)
        to_write += " 50"
        to_write += " " + self.port_type
        to_write += " ~"
        to_write += " 0\n"
        text = remove_quote(self.text)
        text = text.replace("\\\"", "\"")
        to_write += text
        to_write += "\n"
        return [to_write]

# Text GLabel 2200 1600 0    60   Input ~ 0
# "test"


class KicadSchematicComponent(object):
    """ Create the componet in the schematic """

    _L_KEYS = ['name', 'ref']
    _U_KEYS = ['unit', 'convert', 'time_stamp']
    _P_KEYS = ['posx', 'posy']
    _AR_KEYS = ['path', 'ref', 'part']
    _F_KEYS = ['id', 'ref', 'orient', 'posx', 'posy', 'size', 'attributs',
               'hjust', 'props', 'name']

    _KEYS = {'L':_L_KEYS, 'U':_U_KEYS, 'P':_P_KEYS, 'AR':_AR_KEYS, 'F':_F_KEYS}

    def __init__(self, name, ref):
        self.name = name

        self.labels = {}
        self.unit = {}
        self.position = {}
        self.references = []
        self.fields = []


        ref = decode_special_char(ref)

        values = [name, ref]
        self.labels = dict(zip(self._L_KEYS, values))

        timestamp = str(hex(int(time.time()))[2:]).upper()
        values = ['1', '1', timestamp]
        self.unit = dict(zip(self._U_KEYS, values))

        self.unit_part = '1'
        self.orientation = "R0"

    def set_orientation(self, orientation):
        """ Sets the component orientation
            R0, R90, R270, MX, MY, MXR90, MYR90
        """
        #print self.name, "set_orientation:", orientation
        self.orientation = orientation

    #def get_orientation(self):
    #    return self.orientation

    def set_position(self, xpos, ypos):
        """ Sets the KiCad x, y position of the component """
        self.position = {'posx':xpos, 'posy':ypos}
        #self.position = [xpos, ypos]

    #def get_position(self):
    #    """ Returns the component orientaiton """
    #    return self.position

    def add_field(self, field_data):
        """ Adds a new KiCAD 'F n' field to the component """
        def_field = {'id':None, 'ref':None,
                     'orient':'H',
                     'posx':'0',
                     'posy':'0',
                     'size':'50',
                     'attributs':'0000',
                     'hjust':'C',
                     'props':'CNN',
                     'name':''}

        # pylint: disable=W0105
        """
        field_data['posx'], field_data['posy'] = \
                    convert_kicad_coor(field_data['posx'], field_data['posy'])
        """

        for key, value in field_data.items():
            field_data[key] = decode_special_char(str(value))

        # merge dictionaries and set the id value
        field = dict(list(def_field.items()) + list(field_data.items()))
        field['id'] = str(len(self.fields))

        self.fields.append(field)
        return field



    def output(self):
        """ Write the component as KiCad schematic strings """
        rot_mat = RotMat()


        to_write = '$Comp\n'

        component = self

        if component.labels:
            line = 'L '
            # pylint: disable=W0212
            for key in component._L_KEYS:
                line += component.labels[key] + ' '
            to_write += line.rstrip() + '\n'

        if component.unit:
            line = 'U '
            # pylint: disable=W0212
            for key in component._U_KEYS:
                line += component.unit[key] + ' '
            to_write += line.rstrip() + '\n'

        if component.position:
            line = 'P '
            # pylint: disable=W0212
            for key in component._P_KEYS:
                line += str(component.position[key]) + ' '
            to_write += line.rstrip() + '\n'

        for reference in component.references:
            if component.references:
                line = 'AR '
            # pylint: disable=W0212
                for key in component._AR_KEYS:
                    line += reference[key] + ' '
                to_write += line.rstrip() + '\n'

        for field in component.fields:
            line = 'F '
            # pylint: disable=W0212
            for key in component._F_KEYS:
                line += field[key] + ' '
            to_write += line.rstrip() + '\n'

        # pylint: disable=W0105
        """
        to_write += ['\t' + self.unit_part + " "
                     + self.position['posx'] + " "
                     + self.position['posy']] + ['\n']
        """

        str_pos = ' '
            # pylint: disable=W0212
        for key in component._P_KEYS:
            str_pos += str(component.position[key]) + ' '

        to_write += '\t' +  self.unit_part + str_pos + '\n'
        #print self.orientation
        to_write += '\t' + str(rot_mat.str_matrice(self.orientation)) + '\n'
        to_write += '$EndComp\n'

        return [to_write]


# pylint: disable=W0105
"""
class Kicad_Sheet(object):
    _S_KEYS = ['topLeftPosx', 'topLeftPosy','botRightPosx', 'botRightPosy']
    _U_KEYS = ['uniqID']
    _F_KEYS = ['id', 'value', 'IOState', 'side', 'posx', 'posy', 'size']

    _KEYS = {'S':_S_KEYS, 'U':_U_KEYS, 'F':_F_KEYS}

    def __init__(self, data):
        self.shape = {}
        self.unit = {}
        self.fields = []
"""



class KicadSchematic(object):
    """ Manages a KiCad schematic file """
    def __init__(self, filename, project_name):
        self.filename = filename
        self.project_name = project_name
        self.kicad_object_list = []

    def add_kicad_object(self, kicad_object):
        """ Add a schematic element to the schematic """

        if kicad_object != None:
            self.kicad_object_list.append(kicad_object)


    def __output(self, kicad_element):
        """ Local method to expand a list of objects to strings """
        to_write = []
        if isinstance(kicad_element, list):
            for ele in kicad_element:
                to_write += self.__output(ele)
        else:
            to_write += kicad_element.output()
            #for line in to_write:
            #   print line,
        return to_write



    def output(self):
        """ Write all schematic elements to the schematic """

        #pprint.pprint(self.kicad_object_list)

        to_write = self.__output(self.kicad_object_list)

        return to_write


    def save(self, filename=None):
        """ Save the schematic to a schematic file """

        if not filename:
            filename = self.filename + ".sch"

        to_write = []

        template_header_sch = ['EESchema Schematic File Version 2',
                               'LIBS:'+self.project_name+'-cache',
                               'EELAYER 25 0',
                               'EELAYER END',
                               '$Descr A3 16535 11693',
                               'encoding utf-8',
                               'Sheet 1 1',
                               'Title ""',
                               'Date "',
                               'Rev ""',
                               'Comp ""',
                               'Comment1 ""',
                               'Comment2 ""',
                               'Comment3 ""',
                               'Comment4 ""',
                               '$EndDescr']

        for prop in template_header_sch:
            to_write += [prop + "\n"]

        to_write += self.output()

        to_write += ['$EndSCHEMATC']
        to_write += ['\n']

        schematic_file = open(filename, 'w')
        schematic_file.writelines(to_write)
        schematic_file.close()
