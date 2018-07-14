#!/usr/bin/env python
""" Parses an EDIF file and generates a KiCAD library (*-cache.lib) file """

from kicad_lib import *
from kicad_common import *

#from Edif_parser_mod import *
from Edif_parser_mod import \
            search_edif_objects, \
            Read_Edif_file, \
            extract_edif_str_param, \
            extract_edif_pt

def extract_connections(library_component, port_impl_list, port_list):
    """ Wrapper for extract_offset_connections with no offset """
    return extract_offset_connections(library_component,
                                      port_impl_list, port_list, 0, 0)

def extract_offset_connections(library_component, port_impl_list,
                               port_list, offset_x, offset_y):
    """ Extract EDIF pin connections from EDIF with offset x, y """
    for port_impl in port_impl_list:

        i_name = port_impl.get_object("name")
        if i_name != None:
            port_impl_p_name = i_name.get_param(0)

            if port_impl_p_name != None:
                #print "port_impl_p_name =", port_impl_p_name

                pin_name, pin_type, pin_number = \
                        extract_pin_parameters(port_impl_p_name, port_list)
                #print pin_name, pin_type, pin_number

                if pin_number != None:
                    connection = KicadConnection(pin_number, pin_name)
                    connection.set_offset(offset_x, offset_y)
                    dot_pt = \
                        port_impl.get_object("connectLocation.figure.dot.pt")
                    if dot_pt != None:
                        dot_x, dot_y = \
                                convert_kicad_coor(extract_edif_pt(dot_pt))

                    ptl_pin = port_impl.get_object("figure.path.pointList")
                    if ptl_pin != None:
                        xstart, ystart = \
                            convert_kicad_coor(
                                extract_edif_pt(ptl_pin.get_param(0)))
                        xend, yend = \
                            convert_kicad_coor(
                                extract_edif_pt(ptl_pin.get_param(1)))
                        # xstart = dot_x
                        # ystart = dot_y
                        connection.set_pin(xstart, ystart, xend, yend)

                    library_component.add_connection(connection)
    return

def extract_point_list(library_component, point_list):
    """ Wrapper for extract_offset_point_list with no offset """
    return extract_offset_point_list(library_component, point_list, 0, 0)

def extract_offset_point_list(library_component, point_list,
                              offset_x, offset_y):
    """ Extract EDIF point list (segments) with offset x, y """
    for ptl in point_list:
        poly = KicadPoly()
        poly.set_offset(offset_x, offset_y)
        points = search_edif_objects(ptl, "pt")
        for pointxy in points:
            xpos, ypos = convert_kicad_coor(extract_edif_pt(pointxy))
            poly.add_segment(xpos, ypos)
        library_component.add_draw(poly)
    return

def extract_arc_point_list(library_component, point_list):
    """ Wrapper for extract_offset arc_point_list """
    return extract_offset_arc_point_list(library_component,
                                         point_list, 0, 0)

def extract_offset_arc_point_list(library_component, point_list,
                                  offset_x, offset_y):
    """ Extract EDIF arc points with offset x, y  to KiCad arc """
    for ptl in point_list:
        arc = KicadArc()
        arc.set_offset(offset_x, offset_y)
        points = search_edif_objects(ptl, "pt")
        for pointxy in points:
            xpos, ypos = convert_kicad_coor(extract_edif_pt(pointxy))
            arc.add_point(xpos, ypos)
        library_component.add_draw(arc)
    return

def extract_path(library_component, path_list):
    """ Wrapper for extract_offset_path """
    return extract_offset_path(library_component, path_list, 0, 0)

def extract_offset_path(library_component, path_list, offset_x, offset_y):
    """ Extract EDIF path points with offset x, y coordinates """
    for path in path_list:
        point_list = search_edif_objects(path, "pointList")
        extract_offset_point_list(library_component, point_list,
                                  offset_x, offset_y)
    return

def extract_drawing(library_component, figure_list):
    """ Wrapper for extract_offset_drawing with no offset """
    return extract_offset_drawing(library_component, figure_list, 0, 0)

def extract_offset_drawing(library_component, figure_list,
                           offset_x, offset_y):
    """ Extract EDIF drawing with offset x, y to KiCad drawing """

    for figure in figure_list:
        figure_type = extract_edif_str_param(figure, 0)
        if figure_type != None:
            path_list = search_edif_objects(figure, "path")
            extract_offset_path(library_component, path_list,
                                offset_x, offset_y)

        point_list = figure.get_object("polygon.pointList")
        if point_list != None:
            extract_offset_point_list(library_component, [point_list],
                                      offset_x, offset_y)

        arc_point_list = figure.get_object("openShape.curve.arc")
        if arc_point_list != None:
            extract_offset_arc_point_list(library_component, [arc_point_list],
                                          offset_x, offset_y)

        rectangle = figure.get_object("rectangle")
        if rectangle != None:
            xstart, ystart = \
                convert_kicad_coor(extract_edif_pt(rectangle.get_param(0)))
            xend, yend = \
                convert_kicad_coor(extract_edif_pt(rectangle.get_param(1)))
            rectangle = KicadRectangle(xstart, ystart, xend, yend)
            rectangle.set_offset(offset_x, offset_y)
            library_component.add_draw(rectangle)

        circle = figure.get_object("circle")
        if circle != None:
            xstart, ystart = \
                    convert_kicad_coor(extract_edif_pt(circle.get_param(0)))
            xend, yend = \
                    convert_kicad_coor(extract_edif_pt(circle.get_param(1)))
            circle = KicadCircle(xstart, ystart, xend, yend)
            circle.set_offset(offset_x, offset_y)
            library_component.add_draw(circle)

    return


def extract_pin_parameters(port_impl_p_name, port_list):
    """ Extract EDIF component pin parameters (text) """

    pin_name = None
    pin_type = None
    pin_number = None

    for port in port_list:

        if extract_edif_str_param(port, 0)[0] == port_impl_p_name:
            #print port_impl_p_name, "found"
            properties = search_edif_objects(port, "property")

            for prop in properties:
                p1_name = remove_quote(extract_edif_str_param(prop, 0)[1])
                string = \
                    remove_quote(prop.get_object("string").get_param(0))
                #print p1_name, ":", string

                if p1_name == "Name":
                    pin_name = string
                elif p1_name == "Type":
                    pin_type = string
                elif p1_name == "PackagePortNumbers":
                    pin_number = string

    return [pin_name, pin_type, pin_number]

def find_edif_points_maxmin(point_list, maxmin_xy):
    """ Finds the max and min x, y in an EDIF point list """
    max_x = maxmin_xy[0][0]
    max_y = maxmin_xy[0][1]
    min_x = maxmin_xy[1][0]
    min_y = maxmin_xy[1][1]
    #print "maxmin: max_xy " + str([max_x, max_y]) \
    #      + ", min_xy " + str([min_x, min_y])
    for point in point_list:
        points = search_edif_objects(point, "pt")
        for pointxy in points:
            xpos, ypos = convert_kicad_coor(extract_edif_pt(pointxy))
            if xpos > max_x:
                max_x = xpos
            if ypos > max_y:
                max_y = ypos
            if xpos < min_x:
                min_x = xpos
            if ypos < min_y:
                min_y = ypos

    return [max_x, max_y], [min_x, min_y]

def extract_powerobject_symbol(library_component, name, figure_list):
    """ Extracts EDIF powerobject, a type of port """
    is_ground = False
    symbol_info = {'is_valid':True, 'is_ground':False,
                   'min_x':0, 'min_y':0, 'max_x':0, 'max_y':0}
    max_x = -2**32
    max_y = -2**32
    min_x = 2**32
    min_y = 2**32
    x_offset = 0
    y_offset = 0

    figure = figure_list[0]
    figure_group_override = figure.get_object("figureGroupOverride")
    if figure_group_override != None:
        figure_name = figure_group_override.get_param(0)
    else:
        figure_name = figure.get_param(0)

    if figure_name == "POWEROBJECT":
        ref = "#PWR"
        max_xy = [max_x, max_y]
        min_xy = [min_y, min_y]
        for figure in figure_list:
            path_list = search_edif_objects(figure, "path")
            if len(path_list) != 0:
                for path in path_list:
                    point_list = search_edif_objects(path, "pointList")
                    max_xy, min_xy = find_edif_points_maxmin(point_list,
                                                             [max_xy, min_xy])
            circle = search_edif_objects(figure, "circle")
            if len(circle) != 0:
                print " found circle in POWEROBJECT"
                max_xy, min_xy = find_edif_points_maxmin(circle,
                                                         [max_xy, min_xy])
            rectangle = search_edif_objects(figure, "rectangle")
            if len(rectangle) != 0:
                print " found rect in POWEROBJECT"
                max_xy, min_xy = find_edif_points_maxmin(rectangle,
                                                         [max_xy, min_xy])

            #print "POWEROBJECT: max_xy " + str(max_xy) \
            #      + ", min_xy " + str(min_xy)
        max_x = max_xy[0]
        max_y = max_xy[1]
        min_x = min_xy[0]
        min_y = min_xy[1]

        connection = KicadConnection("1", name)
        x_offset = -(min_x + (max_x - min_x) / 2)
        if name in set(['GND', 'DGND', 'AGND', 'EARTH', 'GND_POWER']):
            y_offset = 0
            connection.set_pin(0, 0, 0, -1)
            is_ground = True
        else:
            y_offset = (max_y - min_y)
            connection.set_pin(0, 0, 0, 1)

        library_component.set_powerobject(True)

        library_component.add_connection(connection)
        extract_offset_drawing(library_component, figure_list,
                               x_offset, y_offset)
    else:
        symbol_info['is_valid'] = False
        print "ERROR: could not extract power symbol"
        return
    #print "x_offset = " + str(x_offset) + ", y_offset = " + str(y_offset)
    #print "(" + name + " figures captured for " + ref + ", " + str(max_x) \
    #      + ", " + str(max_y) + "; " + str(min_x) + ", " + str(min_y) + ")"

    symbol_info['is_ground'] = is_ground
    symbol_info['min_x'] = min_x
    symbol_info['min_y'] = min_y
    symbol_info['max_x'] = max_x
    symbol_info['max_y'] = max_y
    return symbol_info

def get_edif_string_anchor(prop):
    """ Helper function: get x, y anchor for string """
    xpos, ypos = [0, 0]

    string = prop.get_object("string")
    if string != None:
        string_display = string.get_object("stringDisplay")
    else:
        string_display = prop.get_object("stringDisplay")

    if string_display != None:
        value = string_display.get_param(0)
        pointxy = string_display.get_object("display.origin.pt")
        if pointxy != None:
            xpos, ypos = convert_kicad_coor(extract_edif_pt(pointxy))
    else:
        print "WARN: string with no point in EDIF as " \
              + str(extract_edif_str_param(string, 0)[0])

    return [xpos, ypos]

def _extract_component_view(view, library_component):
    """ Extracts an EDIF component or drawing entity to KiCad """
    view_name = extract_edif_str_param(view, 0)
    ref = "?"
    xpos = int(0)
    ypos = int(0)
    value_x = int(0)
    value_y = int(0)
    visible = "V"
    orientation = "H"
    hvjustify = text_justify("CENTERCENTER", "R0", "R0")

    interface = view.get_object("interface")
    if interface != None:
        symbol = interface.get_object("symbol")
        if symbol != None:
            prop_list = search_edif_objects(symbol, "property")
            if prop_list != None:
                for prop in prop_list:
                    prop_type = extract_edif_str_param(prop, 0)[0]
                    if prop_type == "VALUE":
                        value_x, value_y = get_edif_string_anchor(prop)
                    elif prop_type == "PIN_NAMES_VISIBLE":
                        string = prop.get_object("string")
                        if string != None:
                            pin_names_visible = \
                                remove_quote(extract_edif_str_param(string, 0)[1])
                            if pin_names_visible == "False":
                                library_component.set_pin_names_visible(False)
                    elif prop_type == "PIN_NUMBERS_VISIBLE":
                        string = prop.get_object("string")
                        if string != None:
                            pin_numbers_visible = \
                                remove_quote(extract_edif_str_param(string, 0)[1])
                            if pin_numbers_visible == "False":
                                library_component.set_pin_numbers_visible(False)

            figure_list = search_edif_objects(symbol, "figure")
            extract_drawing(library_component, figure_list)

            port_impl_list = search_edif_objects(symbol, "portImplementation")
            port_list = search_edif_objects(interface, "port")
            extract_connections(library_component, port_impl_list, port_list)

        designator = interface.get_object("designator")
        if designator != None:
            #print "designator = "+extract_str_param(designator, 0)[1]
            ref = extract_edif_str_param(designator, 0)[1]
            ref = remove_quote(ref)
            if ref.endswith('?'):
                ref = ref[:-1]
            #pointxy = get_edif_string_anchor(designator)
            #print "pointxy = " + str(pointxy)
            string_display = designator.get_object("stringDisplay")
            if string_display != None:
                print "Info: found extra information in reference designator:"
                pointxy = string_display.get_object("display.origin.pt")
                if pointxy != None:
                    print "  " + str(extract_edif_pt(pointxy))
#                   xpos, ypos = convert_kicad_coor(extract_edif_pt(pointxy))
#               display_justify = string_display.get_object("display.justify")
#               if display_justify != None:
#                   hvjustify = text_justify(display_justify.get_param(0),
#                                            "R0")
#                   print "JUSTIFY with " + str(hvjustify)
            else:
                pointxy = \
                    interface.get_object("symbol.keywordDisplay.\
                                         display.origin.pt")
                if pointxy != None:
                    xpos, ypos = convert_kicad_coor(extract_edif_pt(pointxy))

                display_justify = \
                    interface.get_object("symbol.keywordDisplay.\
                                          display.justify")
                if display_justify != None:
                    hvjustify = text_justify(display_justify.get_param(0),
                                             "R0", "R0")
                    #print "JUSTIFY with " + str(hvjustify)

    contents = view.get_object("contents")
    if contents != None:
        figure_list = search_edif_objects(contents, "figure")
        figure = figure_list[0]
        figure_group_override = figure.get_object("figureGroupOverride")
        if figure_group_override != None:
            figure_name = figure_group_override.get_param(0)
        else:
            figure_name = figure.get_param(0)

        if figure_name == "POWEROBJECT":
            power_symbol = extract_powerobject_symbol(library_component,
                                                      view_name[0],
                                                      figure_list)
            if power_symbol['is_valid'] == True:
                if power_symbol['is_ground'] == True:
                    #print "**** GND"
                    xpos = 0
                    ypos = power_symbol['min_y']
                    value_x = 0
                    value_y = power_symbol['min_y'] - 100
                else:
                    #print "**** POWER"
                    xpos = 0
                    ypos = power_symbol['min_y']
                    value_x = 0
                    value_y = power_symbol['max_y'] + 100
                visible = "V"
                orientation = "V"
                ref = "#PWR"
                library_component.set_pin_names_visible(False)
                library_component.set_pin_numbers_visible(False)
    # pylint: disable=W0105
    """
    #
    # GND
    #
    DEF GND #PWR 0 0 Y Y 1 F P
    F0 "#PWR" 0 -250 50 H I C CNN
    F1 "GND" 0 -150 50 H V C CNN
    F2 "" 0 0 50 H I C CNN
    F3 "" 0 0 50 H I C CNN
    DRAW
    P 6 0 1 0 0 0 0 -50 50 -50 0 -100 -50 -50 0 -50 N
    X GND 1 0 0 0 D 50 50 1 1 W N
    ENDDRAW
    ENDDEF

    #
    # +3V3
    #
    DEF +3V3 #PWR 0 0 Y Y 1 F P
    F0 "#PWR" 0 -150 50 H I C CNN
    F1 "+3V3" 0 140 50 H V C CNN
    F2 "" 0 0 50 H I C CNN
    F3 "" 0 0 50 H I C CNN
    ALIAS +3.3V
    DRAW
    P 2 0 1 0 -30 50 0 100 N
    P 2 0 1 0 0 0 0 100 N
    P 2 0 1 0 0 100 30 50 N
    X +3V3 1 0 0 0 U 50 50 1 1 W N
    ENDDRAW
    ENDDEF
    """
    library_component.set_designator(ref)
    #print "x = " + str(xpos) + ", ypos = " + str(ypos) + "; vx = " \
    #      + str(value_x) + ", vy = " + str(value_y) + ";"
    library_component.add_field({'id':0, 'ref':add_quote(ref),
                                 'posx':xpos, 'posy':ypos,
                                 'visible':'I',
                                 'text_align':hvjustify[0],
                                 'props':hvjustify[1] + "NN"})
    library_component.add_field({'id':1, 'ref':add_quote(view_name[0]),
                                 'visible':visible,
                                 'posx':value_x, 'posy':value_y})
    library_component.add_field({'id':2, 'ref':'""', 'posx':0, 'posy':0})
    library_component.add_field({'id':3, 'ref':'""', 'posx':0, 'posy':0})

    return library_component

def extract_kicad_component_library(edif_cell):
    """ Extracts a single EDIF cell (component) from a library """
    cell_name = extract_edif_str_param(edif_cell, 0)
    #cell_name = cell.get_param(0)
    #print cell_name

    view = edif_cell.get_object("view")
    view_name = extract_edif_str_param(view, 0)

    #print view_name[0], view_name[0]

    library_component = KicadLibraryComponent(cell_name[0])

    library_component.add_alias(view_name[0])

    _extract_component_view(view, library_component)

    return library_component

def extract_edif_library_view(view, cell_name, view_index):
    """ Extract a single EDIF component view (convert drawing) """
    view_name = extract_edif_str_param(view, 0)

    library_component = KicadLibraryComponent(view_name[0])

    library_component.add_alias(cell_name[0] + "_" \
                                + chr(ord('A') + view_index))

    _extract_component_view(view, library_component)

    return library_component

def extract_kicad_library(kicad_library, edif_library):
    """ Extracts all components, entities, from EDIF library """

    # Always check for the library name as a parameter of
    # the rename tag, otherwise use the parameter of the
    # library tag
    rename = edif_library.get_object("rename")
    if rename != None:
        library_name = rename.get_param(0)
    else:
        library_name = edif_library.get_param(0)

    print "new library : ", library_name
    cells = search_edif_objects(edif_library, "cell")

    for edif_cell in cells:
        view_list = search_edif_objects(edif_cell, "view")
        if len(view_list) > 1:
            cell_name_as_alias = extract_edif_str_param(edif_cell, 0)
            print "multiview component: " + cell_name_as_alias[0] \
                  + " creates new ones"
            for view in view_list:
                library_component = \
                  extract_edif_library_view(view,
                                            cell_name_as_alias,
                                            view_list.index(view))
                kicad_library.add_component(library_component)
        else:
            library_component = extract_kicad_component_library(edif_cell)
            kicad_library.add_component(library_component)

    return kicad_library
