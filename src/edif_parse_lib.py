#!/usr/bin/env python

from kicad_lib import *

from Edif_parser_mod import *

def extract_connections(library_Component, port_impl_list, port_list):
	return extract_offset_connections(library_Component, port_impl_list, port_list, 0, 0)

def extract_offset_connections(library_Component, port_impl_list, port_list, offset_x, offset_y):

	for port_impl in port_impl_list:

		i_name = port_impl.get_object("name")
		if (i_name!=None):
			port_impl_p_name = i_name.get_param(0)

			if (port_impl_p_name!=None):
				#print "port_impl_p_name =", port_impl_p_name

				pin_name, pin_type, pin_number = extract_pin_parameters(port_impl_p_name, port_list)
				#print pin_name, pin_type, pin_number

				if (pin_number!=None):
					connection = Kicad_Connection(pin_number, pin_name)
					connection.set_offset(offset_x, offset_y)
					dot_pt = port_impl.get_object("connectLocation.figure.dot.pt")
					if (dot_pt!=None):
						dot_x, dot_y = convert_kicad_coor( extract_edif_pt(dot_pt) )

					ptl_pin = port_impl.get_object("figure.path.pointList")
					if (ptl_pin!=None):
						x1, y1 = convert_kicad_coor( extract_edif_pt(ptl_pin.get_param(0)) )
						x2, y2 = convert_kicad_coor( extract_edif_pt(ptl_pin.get_param(1)) )
						# x1 = dot_x
						# y1 = dot_y
						connection.set_pin(x1, y1, x2, y2)

					library_Component.addConnection(connection)
	return

def extract_point_list(library_Component, point_list):
	return extract_offset_point_list(library_Component, point_list, 0, 0)

def extract_offset_point_list(library_Component, point_list, offset_x, offset_y):
	for ptl in point_list:
		poly = Kicad_Poly()
		poly.set_offset(offset_x, offset_y)
		pts = search_edif_objects(ptl, "pt")
		for pt in pts:
			x, y = convert_kicad_coor( extract_edif_pt(pt) )
			poly.add_segment(x, y)
		library_Component.addDraw(poly)
	return

def extract_arc_point_list(library_Component, point_list):
	return extract_offset_arc_point_list(library_Component, point_list, 0, 0)

def extract_offset_arc_point_list(library_Component, point_list, offset_x, offset_y):
	for ptl in point_list:
		arc = Kicad_Arc()
		arc.set_offset(offset_x, offset_y)
		pts = search_edif_objects(ptl, "pt")
		for pt in pts:
			x, y = convert_kicad_coor( extract_edif_pt(pt) )
			arc.add_point(x, y)
		library_Component.addDraw(arc)
	return

def extract_path(library_Component, path_list):
	return extract_offset_path(library_Component, path_list, 0, 0)

def extract_offset_path(library_Component, path_list, offset_x, offset_y):
	for path in path_list:
		point_list = search_edif_objects(path, "pointList")
		extract_offset_point_list(library_Component, point_list, offset_x, offset_y)
	return

#def extract_rectangle(library_Component, )

def extract_drawing(library_Component, figure_list):
	return extract_offset_drawing(library_Component, figure_list, 0, 0)

def extract_offset_drawing(library_Component, figure_list, offset_x, offset_y):

	for figure in figure_list:
		p1 = extract_edif_str_param(figure, 0)
		if (p1!=None):
			path_list = search_edif_objects(figure, "path")
			extract_offset_path(library_Component, path_list, offset_x, offset_y)

		point_list = figure.get_object("polygon.pointList")
		if (point_list!=None):
			extract_offset_point_list(library_Component, [point_list], offset_x, offset_y)

		arc_point_list = figure.get_object("openShape.curve.arc")
		if (arc_point_list!=None):
			extract_offset_arc_point_list(library_Component, [arc_point_list], offset_x, offset_y)

		rectangle = figure.get_object("rectangle")
		if (rectangle!=None):
			x1, y1 = convert_kicad_coor( extract_edif_pt(rectangle.get_param(0)) )
			x2, y2 = convert_kicad_coor( extract_edif_pt(rectangle.get_param(1)) )
			rectangle = Kicad_Rectangle(x1, y1, x2, y2)
			rectangle.set_offset(offset_x, offset_y)
			library_Component.addDraw(rectangle)

		circle = figure.get_object("circle")
		if (circle!=None):
			x1, y1 = convert_kicad_coor( extract_edif_pt(circle.get_param(0)))
			x2, y2 = convert_kicad_coor( extract_edif_pt(circle.get_param(1)))
			circle = Kicad_Circle(x1, y1, x2, y2)
			circle.set_offset(offset_x, offset_y)
			library_Component.addDraw(circle)

	return


def extract_pin_parameters(port_impl_p_name, port_list):

	pin_name = None
	pin_type = None
	pin_number = None

	for port in port_list:

		if ( extract_edif_str_param(port, 0)[0]==port_impl_p_name):
			#print port_impl_p_name, "found"
			properties = search_edif_objects(port, "property")

			for property in properties:
				p1_name = remove_quote( extract_edif_str_param(property, 0)[1] )
				string = remove_quote( property.get_object("string").get_param(0) )
				#print p1_name, ":", string

				if (p1_name=="Name"):
					pin_name = string
				elif (p1_name=="Type"):
					pin_type = string
				elif (p1_name=="PackagePortNumbers"):
					pin_number = string

	return [pin_name, pin_type, pin_number]

def find_edif_points_maxmin(point_list, maxmin_xy):
	max_x = maxmin_xy[0][0]
	max_y = maxmin_xy[0][1]
	min_x = maxmin_xy[1][0]
	min_y = maxmin_xy[1][1]
	#print "maxmin: max_xy " + str([max_x, max_y]) + ", min_xy " + str([min_x, min_y])
	for point in point_list:
		pts = search_edif_objects(point, "pt")
		for pt in pts:
			x, y = convert_kicad_coor( extract_edif_pt(pt) )
			if (x > max_x):
				max_x = x
			if (y > max_y):
				max_y = y
			if (x < min_x):
				min_x = x
			if (y < min_y):
				min_y = y

	return [max_x, max_y], [min_x, min_y]

def extract_powerobject_symbol(library_Component, name, figure_list):
	is_ground = False
	symbol_info = {'is_valid':True,'is_ground':False, 'min_x':0, 'min_y':0, 'max_x':0, 'max_y':0}
	max_x = -2**32
	max_y = -2**32
	min_x = 2**32
	min_y = 2**32
	x_offset = 0
	y_offset = 0

	figure = figure_list[0]
	figureGroupOverride = figure.get_object("figureGroupOverride")
	if (figureGroupOverride!=None):
		figure_name = figureGroupOverride.get_param(0)
	else:
		figure_name = figure.get_param(0)

	if (figure_name=="POWEROBJECT"):
		ref = "#PWR"
		max_xy = [max_x, max_y]
		min_xy = [min_y, min_y]
		for figure in figure_list:
			path_list = search_edif_objects(figure, "path")
			if (len(path_list)!=0):
				for path in path_list:
					point_list = search_edif_objects(path, "pointList")
					max_xy, min_xy = find_edif_points_maxmin(point_list, [max_xy, min_xy])
			circle = search_edif_objects(figure, "circle")
			if (len(circle)!=0):
				print " found circle in POWEROBJECT"
				max_xy, min_xy = find_edif_points_maxmin(circle, [max_xy, min_xy])
			rectangle = search_edif_objects(figure, "rectangle")
			if (len(rectangle)!=0):
				print " found rect in POWEROBJECT"
				max_xy, min_xy = find_edif_points_maxmin(rectangle, [max_xy, min_xy])

			#print "POWEROBJECT: max_xy " + str(max_xy) + ", min_xy " + str(min_xy)
		max_x = max_xy[0]
		max_y = max_xy[1]
		min_x = min_xy[0]
		min_y = min_xy[1]

		connection = Kicad_Connection("1", name)
		x_offset = -(min_x + (max_x - min_x) / 2)
		if (name in set(['GND', 'DGND', 'AGND', 'EARTH', 'GND_POWER'])):
			#y_offset = -100 # negative number works
			y_offset = 0
			#y_offset = -(min_y + (max_y - min_y) / 2)
			connection.set_pin(0, 0, 0, -1)
			is_ground = True
		else:
			y_offset = (max_y - min_y)
			connection.set_pin(0, 0, 0, 1)

		library_Component.set_powerobject(True)

		library_Component.addConnection(connection)
		extract_offset_drawing(library_Component, figure_list, x_offset, y_offset)
	else:
		symbol_info['is_valid'] = False
		print "ERROR: could not extract power symbol"
		return
	#print "x_offset = " + str(x_offset) + ", y_offset = " + str(y_offset)
	#print "(" + name + " figures captured for " + ref + ", " + str(max_x) + ", " + str(max_y) + "; " + str(min_x) + ", " + str(min_y) + ")"

	symbol_info['is_ground'] = is_ground
	symbol_info['min_x'] = min_x
	symbol_info['min_y'] = min_y
	symbol_info['max_x'] = max_x
	symbol_info['max_y'] = max_y
	return symbol_info

def _extract_component_view(view, library_Component):
	view_name = extract_edif_str_param(view, 0)
	ref="?"
	x = int(0)
	y = int(0)
	value_x = int(0)
	value_y = int(0)
	visible = "V"
	orientation = "H"
	hvjustify = text_justify("CENTERCENTER", "R0", "R0")

	interface = view.get_object("interface")
	if (interface!=None):
		symbol  = interface.get_object("symbol")
		if (symbol!=None):
			property_list = search_edif_objects(symbol, "property")
			if (property_list!=None):
				for property in property_list:
					p1 = extract_edif_str_param(property, 0)[0]
					if (p1=="VALUE"):
						string = property.get_object("string")
						if (string!=None):
							stringDisplay = string.get_object("stringDisplay")
							if (stringDisplay!=None):
								#value = normalize_edif_string(str(stringDisplay.get_param(0)))
								value = stringDisplay.get_param(0)
								pt = stringDisplay.get_object("display.origin.pt")
								if (pt!=None):
									value_x, value_y = convert_kicad_coor( extract_edif_pt(pt) )
							else:
								print "ASSERT: unexpected missing stringDisplay in EDIF as " + str(extract_edif_str_param(string, 0)[0])
					elif (p1=="PIN_NAMES_VISIBLE"):
						string = property.get_object("string")
						if (string!=None):
							pin_names_visible = remove_quote(extract_edif_str_param(string, 0)[1])
							if (pin_names_visible=="False"):
								library_Component.set_pin_names_visible(False)
					elif (p1=="PIN_NUMBERS_VISIBLE"):
						string = property.get_object("string")
						if (string!=None):
							pin_numbers_visible = remove_quote(extract_edif_str_param(string, 0)[1])
							if (pin_numbers_visible=="False"):
								library_Component.set_pin_numbers_visible(False)

			figure_list = search_edif_objects(symbol, "figure")
			extract_drawing(library_Component, figure_list)

			port_impl_list = search_edif_objects(symbol, "portImplementation")
			port_list = search_edif_objects(interface, "port")
			extract_connections(library_Component, port_impl_list, port_list)

		designator = interface.get_object("designator")
		if (designator!=None):
			#print "designator = "+extract_str_param(designator, 0)[1]
			ref = extract_edif_str_param(designator, 0)[1]
			ref = remove_quote(ref)
			if (ref.endswith('?')):
				ref = ref[:-1]
			stringDisplay = designator.get_object("stringDisplay")
			if (stringDisplay!=None):
				print "Info: found extra information in reference designator:"
				pt = stringDisplay.get_object("display.origin.pt")
				if (pt!=None):
					print "  " + str(extract_edit_pt(pt))
#					x, y = convert_kicad_coor( extract_edif_pt(pt) )

#				display_justify = stringDisplay.get_object("display.justify")
#				if (display_justify!=None):
#					hvjustify = text_justify(display_justify.get_param(0), "R0")
#					print "JUSTIFY with " + str(hvjustify)
			else:
				pt = interface.get_object("symbol.keywordDisplay.display.origin.pt")
				if (pt!=None):
					x, y = convert_kicad_coor( extract_edif_pt(pt) )

				display_justify = interface.get_object("symbol.keywordDisplay.display.justify")
				if (display_justify!=None):
					hvjustify = text_justify(display_justify.get_param(0), "R0", "R0")
					#print "JUSTIFY with " + str(hvjustify)

	contents =  view.get_object("contents")
	if (contents!=None):
		figure_list = search_edif_objects(contents, "figure")
		figure = figure_list[0]
		figureGroupOverride = figure.get_object("figureGroupOverride")
		if (figureGroupOverride!=None):
			figure_name = figureGroupOverride.get_param(0)
		else:
			figure_name = figure.get_param(0)

		if (figure_name=="POWEROBJECT"):
			power_symbol = extract_powerobject_symbol(library_Component, view_name[0], figure_list)
			if (power_symbol['is_valid']==True):
				if (power_symbol['is_ground']==True):
					#print "**** GND"
					x = 0
					y = power_symbol['min_y']
					value_x = 0
					value_y = power_symbol['min_y'] - 100
				else:
					#print "**** POWER"
					x = 0
					y = power_symbol['min_y']
					value_x = 0
					value_y = power_symbol['max_y'] + 100
				visible = "V"
				orientation = "V"
				ref="#PWR"
				library_Component.set_pin_names_visible(False)
				library_Component.set_pin_numbers_visible(False)
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
	library_Component.set_designator(ref)
	#print "x = " + str(x) + ", y = " + str(y) + "; vx = " + str(value_x) + ", vy = " + str(value_y) + ";"
	library_Component.addField({'id':0, 'ref':add_quote(ref), 'posx':x, 'posy':y, 'visible':'I', 'text_align':hvjustify[0], 'props':hvjustify[1] + "NN"})
#	library_Component.addField({'id':1, 'ref':add_quote(view_name[0]), 'posx':value_x, 'posy':value_y, 'visible':'I', 'text_orientation':orientation})
#	library_Component.addField({'id':0, 'ref':add_quote(ref), 'posx':x, 'posy':y})
	library_Component.addField({'id':1, 'ref':add_quote(view_name[0]), 'visible':visible, 'posx':value_x, 'posy':value_y})
	library_Component.addField({'id':2, 'ref':'""', 'posx':0, 'posy':0})
	library_Component.addField({'id':3, 'ref':'""', 'posx':0, 'posy':0})

	return library_Component

def extract_kicad_component_library(edif_cell):
	cell_name = extract_edif_str_param(edif_cell, 0)
	#cell_name = cell.get_param(0)
	#print cell_name

	view = edif_cell.get_object("view")
	view_name = extract_edif_str_param(view, 0)

	#print view_name[0], view_name[0]

	library_Component = Kicad_Library_Component(cell_name[0])

	library_Component.addAlias(view_name[0])

	_extract_component_view(view, library_Component)

	return library_Component

def extract_kicad_component_view_library(view, cell_name, view_index):
	view_name = extract_edif_str_param(view, 0)

	library_Component = Kicad_Library_Component(view_name[0])

	library_Component.addAlias(cell_name[0] + "_" + chr( ord('A') + view_index))

	_extract_component_view(view, library_Component)

	return library_Component

def extract_kicad_library(kicad_library, edif_library):

	# Always check for the library name as a parameter of
	# the rename tag, otherwise use the parameter of the
	# library tag
	rename = edif_library.get_object("rename")
	if (rename!=None):
		library_name = rename.get_param(0)
	else:
		library_name = edif_library.get_param(0)

	print "new library : ", library_name
	cells = search_edif_objects(edif_library, "cell")

	for edif_cell in cells:
		view_list = search_edif_objects(edif_cell, "view")
		if (len(view_list) > 1):
			cell_name_as_alias = extract_edif_str_param(edif_cell, 0)
			print "multiview component: " + cell_name_as_alias[0] + " creates new ones"
			for view in view_list:
				library_Component = extract_kicad_component_view_library(view, cell_name_as_alias, view_list.index(view))
				kicad_library.addComponent( library_Component )
		else:
			library_Component = extract_kicad_component_library(edif_cell)
			kicad_library.addComponent( library_Component )

	return kicad_library