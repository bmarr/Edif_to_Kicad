#!/usr/bin/env python
""" Parses an EDIF file and generates a KiCAD schematic (.sch) file """

from kicad_sch import *

#from Edif_parser_mod import *
from Edif_parser_mod import \
            search_edif_objects, \
            Read_Edif_file, \
            extract_edif_str_param, \
            extract_edif_pt

from kicad_common import remove_quote, normalize_edif_string, text_justify

# from KiCAD 4.07 source include/eda_text.txt
TEXT_NO_VISIBLE = int('1', 2)

def eda_attribut_string(attribut_bin):
    # pylint: disable=W0105
    """ Converts binary attribute field to a padded number """

    """ Note: This field is not well defined.
              The field only supports
               bit 0 == 1, hidden
               bit 0 == 0, visible
    """

    return str(int(str(attribut_bin), 2)).zfill(4)

def extract_kicad_text_notes(edif_annotate):
    """ Parse EDIF general text from schematic to KiCad schematic """

    text_notes = []
    height = 60 # fudged
    string_display = edif_annotate.get_object("stringDisplay")
    if string_display != None:
        text = string_display.get_param(0)
        edif_pt = string_display.get_object("display.origin.pt")
        if edif_pt != None:
            xpos, ypos = convert_kicad_coor(extract_edif_pt(edif_pt))
            textnote = KicadTextNote(xpos, ypos)
            textnote.set_text(text)
            figure_group_override = \
                    string_display.get_object("display.figureGroupOverride")
            if figure_group_override != None:
                text_height = figure_group_override.get_object("TextHeight")
                if text_height != None:
                    height = int(text_height.get_param(0))
                    if height >= 12:
                        textnote.set_bold()
            textnote.set_size((float(height) / 11 * 60))
            #print " new text note: " + text
            text_notes.append(textnote)

    if len(text_notes) == 0:
        return None
    else:
        return text_notes
# pylint: disable=W0105
'''
def extract_kicad_noconnection(instance, terminated_pin_pts):
    noconnections = []
    portInstances = search_edif_objects(instance, "portInstance")
    for portInstance in portInstances:
        properties = search_edif_objects(portInstance, "property")
        for prop in properties:
            if prop.get_param(0) == "TERMINATOR":
                string = prop.get_object("string")
                if string != None:
                    if string.get_param(0) == '"TRUE"':

                        # solution ci-dessous ne place pas correctement le symbole X
                        #pt = portInstance.get_object("designator.stringDisplay.display.origin.pt")
                        #if (edif_pt != None):
                            xpos, ypos = convert_kicad_coor(extract_edif_pt(edif_pt))
                            noconnections.append(KicadNoConnection(xpos, ypos))

                        # @TODO : il faut calculer le point a partir du composant dans la librairie :
                        # trop galere pour l'instant ...

    #pprint.pprint(noconnections)
    if len(noconnections) == 0:
        return None
    else:
        return noconnections
'''

def build_kicad_field(prop, ref_xy, symbol_orientation):
    """ Builds a single KiCad schematic "F n" property field:
         F field_number 'text' orientation posX posY size Flags
           hjustify vjustify/italic/bold 'name'

        These properties typically start at F 4, or the 5th
        property of a component and onwards
        Example:
         F 4 "Infineon" H 2300 4500 50 0000 L TNN "Manufacturer"
         F 5 "ESD108-B1-CSP0201" H 2300 4400 50 0000 L TNN
                "Manufacturer Part Number"
         F 6 "D DIODE BIDIRECTIONAL TVS" H 0 0 50 0001 C CNN "Source Package"
         ...

         Returns:
            A dictionary of "F" elements
    """

    prop_attributs = int('0', 2)
    orientation = "H"
    hvjustify = text_justify("CENTERCENTER", "R0", symbol_orientation)
    xpos = 0
    ypos = 0
    property_name = extract_edif_str_param(prop, 0)
    #property_tag = str(property_name[0])
    #print "name = " + str(property_name[1]) + "(" + property_tag + ")"
    name = str(property_name[1])
    string = prop.get_object("string")
    if string != None:
        #value = extract_edif_str_param(string, 0)
        value = str(string.get_param(0))
        #print "value = " + value
        string_display = string.get_object("stringDisplay")
        if string_display != None:
            value = string_display.get_param(0)
            #print "SCH: prop value = " + str(value)
            display_orientation = \
                            string_display.get_object("display.orientation")
            if display_orientation != None:
                prop_orientation = \
                            remove_quote(display_orientation.get_param(0))
            else:
                prop_orientation = "R0"
            orientation = convert_edif_orientation_to_hv(prop_orientation,
                                                         symbol_orientation)

            edif_pt = string_display.get_object("display.origin.pt")
            if edif_pt != None:
                xpos, ypos = convert_kicad_local_coor(extract_edif_pt(edif_pt),
                                                      ref_xy,
                                                      symbol_orientation)
                #print " field xy = " + str([xpos, ypos]) \
                #                     + "orientation = " \
                #                     + symbol_orientation
            if value == '"N/A"':
                prop_attributs = bin(prop_attributs | TEXT_NO_VISIBLE)
            else:
                prop_attributs = int('0', 2)

            display_orientation = \
                            string_display.get_object("display.orientation")
            if display_orientation != None:
                text_orientation = \
                                remove_quote(display_orientation.get_param(0))
            else:
                text_orientation = "R0"
            display_justify = string_display.get_object("display.justify")
            if display_justify != None:
                hvjustify = text_justify(display_justify.get_param(0),
                                         text_orientation,
                                         symbol_orientation)
            figure_group_override = \
                    string_display.get_object("display.figureGroupOverride")
            if figure_group_override != None:
                visible_false = \
                            figure_group_override.get_object("visible.false")
                if visible_false != None:
                    prop_attributs = bin(prop_attributs | TEXT_NO_VISIBLE)
                    #prop_attributs = int('1', 2)
                else:
                    prop_attributs = bin(prop_attributs & ~TEXT_NO_VISIBLE)
                    #prop_attributs = int('0', 2)
        else:
            prop_attributs = bin(prop_attributs | TEXT_NO_VISIBLE)
            #print "ref des coordinates assigned to prop value " \
            #                    + str(value) + " of " + str(property_name[0])
            #value = ""

        f_data = {'ref': value, 'posx':xpos, 'posy':ypos,
                  'attributs':eda_attribut_string(prop_attributs),
                  'orient':orientation, 'hjust':hvjustify[0],
                  'props':hvjustify[1] + "NN", 'name':name}
        return f_data
    return None

def extract_kicad_component(instance):
    """ Extracts a component from EDIF and creates a KiCad component """
    f_data = []
    view_ref = instance.get_object("viewRef")
    cell_ref = view_ref.get_object("cellRef")
    libname = "" + view_ref.get_param(0)
    #libname = "IMPORT_"+cellRef.get_param(0)
    hvjustify = text_justify("CENTERCENTER", "R0", "R0")
    refdes_orientation = "H"
    comp_orientation = "H"
    xpos = 0
    ypos = 0

    # F 0

    string_display = instance.get_object("designator.stringDisplay")
    if string_display == None:
        return None

    ref_design = string_display.get_param(0)
    kicad_component = KicadSchematicComponent(libname, ref_design)

    # component orientation
    instance_orientation = instance.get_object("transform.orientation")
    if instance_orientation != None:
        comp_orientation = remove_quote(instance_orientation.get_param(0))
    else:
        comp_orientation = "R0"

    kicad_component.set_orientation(comp_orientation)

    display_orientation = string_display.get_object("display.orientation")
    if display_orientation != None:
        refdes_orientation = remove_quote(display_orientation.get_param(0))
    else:
        refdes_orientation = "R0"

    refdes_orientation = convert_edif_orientation_to_hv(refdes_orientation,
                                                        comp_orientation)

    # component position - the reference point
    edif_pt = instance.get_object("transform.origin.pt")
    if edif_pt != None:
        component_x, component_y = convert_kicad_coor(extract_edif_pt(edif_pt))
        kicad_component.set_position(component_x, component_y)
        component_xy = [component_x, component_y]

    # Position designator for Kicad coordinates
    #  - designator X is relative to component X for rotation and mirroring
    #  - designator ypos is flipped relative to
    #     component x-axis line of symmetry
    #  - visible properties text is offset from component
    #     relative to designator [xpos, ypos]
    prop_xy = component_xy
    edif_pt = string_display.get_object("display.origin.pt")
    if edif_pt != None:
        xpos, ypos = convert_kicad_local_coor(extract_edif_pt(edif_pt),
                                              component_xy,
                                              comp_orientation)
        prop_xy = convert_kicad_local_coor(extract_edif_pt(edif_pt),
                                           component_xy,
                                           comp_orientation)

    display_orientation = string_display.get_object("display.orientation")
    if display_orientation != None:
        text_orientation = remove_quote(display_orientation.get_param(0))
    else:
        text_orientation = "R0"
    display_justify = string_display.get_object("display.justify")
    if display_justify != None:
        hvjustify = text_justify(display_justify.get_param(0),
                                 text_orientation,
                                 comp_orientation)

    f_data.append({'ref':ref_design, 'posx':xpos, 'posy':ypos,
                   'orient':refdes_orientation, 'hjust':hvjustify[0],
                   'props':hvjustify[1] + "NN"})


    # F 1 "Value"
    properties = search_edif_objects(instance, "property")
    for prop in properties:
        if extract_edif_str_param(prop, 0)[0] == "VALUE":
            f_prop = build_kicad_field(prop, component_xy, comp_orientation)
            if f_prop != None:
                f_data.append(f_prop)

    # F 2 "Footprint"
    for prop in properties:
        if extract_edif_str_param(prop, 0)[0] == "PCB_FOOTPRINT":
            f_prop = build_kicad_field(prop, component_xy, comp_orientation)
            #print str(f_prop)
            if f_prop != None:
                f_data.append(f_prop)

    # F 3 "Data Link"
    f_data.append({'ref': '""', 'posx':component_x,
                   'posy':component_y, 'attributs':'0001'})

    # F 4 and up
    for prop in properties:
        if extract_edif_str_param(prop, 0)[0] != "VALUE":
#           f_prop = build_kicad_field(prop, prop_xy, comp_orientation)
            f_prop = build_kicad_field(prop, component_xy, comp_orientation)
            if f_prop != None:
                f_data.append(f_prop)

    #print value + " " + f1_data['attributs']

    #*******
    for field in f_data:
        kicad_component.add_field(field)

    return kicad_component




def extract_kicad_wires(edif_net):
    """ Extracts a wire from EDIF and creates a KiCad wire """

    wires = []
    xnext, ynext = [0, 0]
    figures = search_edif_objects(edif_net, "figure")
    for figure in figures:
        if figure != None:
            if figure.get_param(0) == "WIRE":
                pts = figure.get_object("path.pointList")
                for i in range(0, pts.get_nb_param()):
                    edif_pt = pts.get_param(i)
                    xpos, ypos = convert_kicad_coor(extract_edif_pt(edif_pt))
                    if i > 0:
                        wire = KicadWire(xnext, ynext, xpos, ypos)
                        wires.append(wire)
                    xnext, ynext = [xpos, ypos]

    if len(wires) == 0:
        return None
    else:
        return wires


def extract_kicad_net_aliases(edif_net):
    """ Extracts a net alias text from EDIF and creates a KiCad net alias """

    net_aliases = []
    net_name = extract_edif_str_param(edif_net, 0)
    if net_name != None:
        if type(net_name[0]) != unicode:
            display_list = search_edif_objects(net_name[0], "display")
            for display in display_list:
                edif_pt = display.get_object("origin.pt")
                if edif_pt != None:
                    xpos, ypos = convert_kicad_coor(extract_edif_pt(edif_pt))
                    #print net_name[1], xpos, y
                    net_alias = \
                        KicadNetAlias(xpos, ypos,
                                      normalize_edif_string(net_name[1]))
                    net_aliases.append(net_alias)

    if len(net_aliases) == 0:
        return None
    else:
        return net_aliases


def extract_kicad_junctions(edif_net):
    """ Extracts a junction from EDIF and creates a KiCad junction """

    junctions = []
    instances = search_edif_objects(edif_net, "instance")
    for instance in instances:
        if instance != None:
            #ident = instance.get_param(0)
            edif_pt = instance.get_object("transform.origin.pt")
            if edif_pt != None:
                xpos, ypos = convert_kicad_coor(extract_edif_pt(edif_pt))
                junction = KicadJunction(xpos, ypos)
                junctions.append(junction)

    if len(junctions) == 0:
        return None
    else:
        return junctions



def extract_kicad_port(edif_port):
    """ Extracts a port from EDIF and creates a KiCad port """

    # portImplementation, pI
    port_is_labeled = False
    hvjustify = text_justify("CENTERCENTER", "R0", "R0")
    refdes_orientation = "H"
    port_orientation = "H"
    porttext_x, porttext_y = [0, 0]

    # p2
    instance = edif_port.get_object("instance")
    p2_name = normalize_edif_string(extract_edif_str_param(instance, 0)[1])
    #print "p2_name = " + str(p2_name)

    view_ref = instance.get_object("viewRef")
    name = view_ref.get_param(0)
    # pylint: disable=W0105
    """
    edif_pt = instance.get_object("transform.origin.pt")
    if edif_pt != None:
        component_x, component_y = extract_pt(edif_pt)
    """
    port_orientation = instance.get_object("transform.orientation")
    if port_orientation != None:
        port_orientation = remove_quote(port_orientation.get_param(0))
    else:
        port_orientation = "R0"

    edif_pt = edif_port.get_object("connectLocation.figure.dot.pt")
    if edif_pt != None:
        component_x, component_y = convert_kicad_coor(extract_edif_pt(edif_pt))
    else:
        return
    #print "x, ypos = " + str([component_x, component_y])
    port_instance = edif_port.get_param(0)

    if type(port_instance) == unicode:
        p_inst_type = None
        p_inst_name = port_instance
        #print "UNICODE: " + str(port_instance)
    else:

        instance = edif_port.get_object("instance")
        if instance != None:
            view_ref = instance.get_object("viewRef")

        p_inst_type = port_instance.get_context()
        if p_inst_type == "name":
            # text module
            p_inst_name = normalize_edif_string(port_instance.get_param(0))
            #print "pI_name = " + str(p_inst_name)

            display = port_instance.get_object("display")
        if display != None:
            p_inst_type = display.get_param(0)
            designator_pt = display.get_object("origin.pt")

            display_orientation = display.get_object("orientation")
            if display_orientation != None:
                text_orientation = \
                                remove_quote(display_orientation.get_param(0))
            else:
                text_orientation = "R0"
            display_justify = display.get_object("justify")
            if display_justify != None:
                hvjustify = text_justify(display_justify.get_param(0),
                                         text_orientation, port_orientation)

            display_orientation = display.get_object("orientation")
            if display_orientation != None:
                refdes_orientation = \
                                remove_quote(display_orientation.get_param(0))
            else:
                refdes_orientation = "R0"

            refdes_orientation = \
                            convert_edif_orientation_to_hv(refdes_orientation,
                                                           port_orientation)

            if designator_pt != None:
                porttext_x, porttext_y = \
                    convert_kicad_local_coor(extract_edif_pt(designator_pt),
                                             [component_x, component_y],
                                             port_orientation)
                port_is_labeled = True

                #print "port " + str(p_inst_name) + " of " \
                # + str(p_inst_type) + " at : " + str(porttext_x) \
                # + ", " + str(porttext_y)

    # TODO: test EDIF MODULETEXT and KicadTextPort class
    if p_inst_type == "MODULETEXT":

        text_port = KicadTextPort(p_inst_name, component_x, component_y)

        name, rot = name.split("_")
        name = name.replace("PORT", "")

        if name == "BOTH":
            port_type = "BiDi"
        elif name == "LEFT":
            port_type = "Output"
        elif name == "RIGHT":
            port_type = "Input"
        else:
            port_type = "UnSpc"

        if rot == "L":
            angle = 1
        else:
            angle = 0


        def_rot = {
            "R0":[0, 2],
            "R90":[3, 1],
            "R180":[2, 0],
            "R270":[1, 3],

            "MY":[2, 0],
            "MYR90":[1, 3],
            #"MYR180":[0, 2],
            #"MYR270":[1, 3],

            "MX":[0, 2],
            "MXR90":[3, 1],
            #"MXR180":[0, 2],
            #"MXR270":[1, 3]
            }
        comb_angle = def_rot[port_orientation][angle]

        #print name, rot, orientation, comb_angle


        text_port.set_text(p2_name[1])
        text_port.set_type(port_type)
        text_port.set_rotation(comb_angle)

        return text_port



    if p_inst_type == "POWERTEXT" or \
        (p_inst_type == None and p_inst_name in {'GND', 'GNDA', 'GNDD',
                                                 'GNDS', 'EARTH',
                                                 'GND_POWER'}):
        ref = "\"#PWR?\""
    else:
        ref = "\"" + name + "\""

    value = "\"" + p_inst_name + "\""

    #x = component_x
    #y = component_y
    xpos, ypos = [porttext_x, porttext_y]

    f0_data = {'ref': ref, 'posx':xpos, 'posy':ypos, 'attributs':'0001'}
    if port_is_labeled == True:
        f1_data = {'ref': value, 'posx':porttext_x, 'posy':porttext_y,
                   'attributs':'0000', 'orient':refdes_orientation,
                   'hjust':hvjustify[0], 'props':hvjustify[1] + "NN"}
    else:
        f1_data = {'ref': value, 'posx':xpos, 'posy':ypos, 'attributs':'0001'}

    f2_data = {'ref': '""', 'posx':component_x,
               'posy':component_y, 'attributs':'0001'}
    f3_data = {'ref': '""', 'posx':component_x,
               'posy':component_y, 'attributs':'0001'}

    kicad_component = KicadSchematicComponent(name, ref)
    kicad_component.set_position(component_x, component_y)
    kicad_component.set_orientation(port_orientation)
    kicad_component.add_field(f0_data)
    kicad_component.add_field(f1_data)
    kicad_component.add_field(f2_data)
    kicad_component.add_field(f3_data)
    return kicad_component
