#!/usr/bin/env python

from kicad_sch import *

from Edif_parser_mod import *

from kicad_common import *

# from KiCAD 4.07 source include/eda_text.txt
TEXT_NO_VISIBLE = int('1', 2)

def eda_attribut_string(attribut_bin):
	return str(int(str(attribut_bin), 2)).zfill(4)

def extract_kicad_text_notes(edif_annotate):
	text_notes = []
	italic = "-"
	bold = 0
	height = 60 # fudged
	stringDisplay = edif_annotate.get_object("stringDisplay")
	if (stringDisplay!=None):
		text = stringDisplay.get_param(0)
		pt = stringDisplay.get_object("display.origin.pt")
		if (pt!=None):
			x, y = convert_kicad_coor( extract_edif_pt(pt) )
			textnote = KicadTextNote(x, y)
			textnote.set_text(text)
			figureGroupOverride = stringDisplay.get_object("display.figureGroupOverride")
			if (figureGroupOverride!=None):
				textHeight = figureGroupOverride.get_object("TextHeight")
				if (textHeight!=None):
					height = int(textHeight.get_param(0))
					if (height >= 12):
						textnote.set_bold()
			textnote.set_size((float(height) / 11 * 60))
			#print " new text note: " + text
			text_notes.append(textnote)

	if (len(text_notes)==0):
		return None
	else:
		return text_notes


def extract_kicad_noconnection(instance, terminated_pin_pts):
	noconnections = []
	portInstances = search_edif_objects(instance, "portInstance")
	for portInstance in portInstances:
		properties = search_edif_objects(portInstance, "property")
		for property in properties:
			if (property.get_param(0)=="TERMINATOR"):
				string = property.get_object("string")
				if (string!=None):
					if (string.get_param(0)=='"TRUE"'):

						# solution ci-dessous ne place pas correctement le symbole X
						#pt = portInstance.get_object("designator.stringDisplay.display.origin.pt")
						#if (pt!=None):
							x, y = convert_kicad_coor( extract_edif_pt(pt) )
							noconnections.append( KicadNoConnection(x, y) )

						# @TODO : il faut calculer le point a partir du composant dans la librairie :
						# trop galere pour l'instant ...

	#pprint.pprint(noconnections)
	if (len(noconnections)==0):
		return None
	else:
		return noconnections

def build_kicad_field(property, ref_xy, symbol_orientation):
	prop_attributs = int('0', 2)
	orientation = "H"
	hvjustify = text_justify("CENTERCENTER", "R0", symbol_orientation)
	x = 0
	y = 0
	property_name = extract_edif_str_param(property, 0)
	property_tag = str(property_name[0])
	#print "name = " + str(property_name[1]) + "(" + property_tag + ")"
	name = str(property_name[1])
	string = property.get_object("string")
	if (string!=None):
		#value = extract_edif_str_param(string, 0)
		value = str(string.get_param(0))
		#print "value = " + value
		stringDisplay = string.get_object("stringDisplay")
		if (stringDisplay!=None):
			value = stringDisplay.get_param(0)
			#print "SCH: prop value = " + str(value)
			display_orientation = stringDisplay.get_object("display.orientation")
			if (display_orientation!=None):
				prop_orientation = remove_quote(display_orientation.get_param(0))
			else:
				prop_orientation = "R0"
			orientation = convert_edif_orientation_to_hv(prop_orientation, symbol_orientation)

			pt = stringDisplay.get_object("display.origin.pt")
			if (pt!=None):
				x, y = convert_kicad_local_coor(extract_edif_pt(pt), ref_xy, symbol_orientation)
				#print " field xy = " + str([x, y]) + "orientation = " + symbol_orientation
			if (value=='"N/A"'):
				prop_attributs = bin(prop_attributs | TEXT_NO_VISIBLE)
			else:
				prop_attributs = int('0', 2)

			display_orientation = stringDisplay.get_object("display.orientation")
			if (display_orientation!=None):
				text_orientation = remove_quote(display_orientation.get_param(0))
			else:
				text_orientation = "R0"
			display_justify = stringDisplay.get_object("display.justify")
			if (display_justify!=None):
				hvjustify = text_justify(display_justify.get_param(0), text_orientation, symbol_orientation)
			figureGroupOverride = stringDisplay.get_object("display.figureGroupOverride")
			if (figureGroupOverride!=None):
				visible_false = figureGroupOverride.get_object("visible.false")
				if (visible_false!=None):
					prop_attributs = bin(prop_attributs | TEXT_NO_VISIBLE)
					#prop_attributs = int('1', 2)
				else:
					prop_attributs = bin(prop_attributs & ~TEXT_NO_VISIBLE)
					#prop_attributs = int('0', 2)
		else:
			prop_attributs = bin(prop_attributs | TEXT_NO_VISIBLE)
			#print "ref des coordinates assigned to property value " + str(value) + " of " + str(property_name[0])
			#value = ""

		f_data = {'ref': value, 'posx':x, 'posy':y,
						'attributs':eda_attribut_string(prop_attributs),
						'orient':orientation, 'hjust':hvjustify[0],
						'props':hvjustify[1] + "NN", 'name':name}
		return f_data
	return None

def extract_kicad_component(instance):

	f_data = []
	viewRef = instance.get_object("viewRef")
	cellRef = viewRef.get_object("cellRef")
	libname = ""+viewRef.get_param(0)
	#libname = "IMPORT_"+cellRef.get_param(0)
	hvjustify = text_justify("CENTERCENTER", "R0", "R0")
	refdes_orientation = "H"
	comp_orientation = "H"
	x = 0
	y = 0

	# F 0

	stringDisplay = instance.get_object("designator.stringDisplay")
	if (stringDisplay==None):
		return None

	refDesign = stringDisplay.get_param(0)
	kicad_component = KicadSchematicComponent(libname, refDesign)

	# component orientation
	instance_orientation = instance.get_object("transform.orientation")
	if (instance_orientation!=None):
		comp_orientation = remove_quote(instance_orientation.get_param(0))
	else:
		comp_orientation = "R0"

	kicad_component.set_orientation(comp_orientation)

	display_orientation = stringDisplay.get_object("display.orientation")
	if (display_orientation!=None):
		refdes_orientation = remove_quote(display_orientation.get_param(0))
	else:
		refdes_orientation = "R0"

	refdes_orientation = convert_edif_orientation_to_hv(refdes_orientation, comp_orientation)

	# component position - the reference point
	pt = instance.get_object("transform.origin.pt")
	if (pt!=None):
		component_x, component_y = convert_kicad_coor( extract_edif_pt(pt) )
		kicad_component.set_position(component_x, component_y)
		component_xy = [component_x, component_y]

	# Position designator for Kicad coordinates
	#  - designator X is relative to component X for rotation and mirroring
	#  - designator y is flipped relative to component x-axis line of symmetry
	#  - visible properties text is offset from component relative to designator [x, y]
	prop_xy = component_xy
	pt = stringDisplay.get_object("display.origin.pt")
	if (pt!=None):
		x, y = convert_kicad_local_coor(extract_edif_pt(pt), component_xy, comp_orientation)
		#prop_xy = convert_kicad_local_coor(extract_edif_pt(pt), [x, y], comp_orientation)
		prop_xy = convert_kicad_local_coor(extract_edif_pt(pt), component_xy, comp_orientation)

	display_orientation = stringDisplay.get_object("display.orientation")
	if (display_orientation!=None):
		text_orientation = remove_quote(display_orientation.get_param(0))
	else:
		text_orientation = "R0"
	display_justify = stringDisplay.get_object("display.justify")
	if (display_justify!=None):
		hvjustify = text_justify(display_justify.get_param(0), text_orientation, comp_orientation)

	f_data.append({'ref':refDesign, 'posx':x, 'posy':y,
					'orient':refdes_orientation, 'hjust':hvjustify[0],
					'props':hvjustify[1] + "NN"})


	# F 1 "Value"
	properties = search_edif_objects(instance, "property")
	for property in properties:
		if (extract_edif_str_param(property, 0)[0]=="VALUE"):
			f_prop = build_kicad_field(property, component_xy, comp_orientation)
			if (f_prop!=None):
				f_data.append(f_prop)

	# F 2 "Footprint"
	for property in properties:
		if (extract_edif_str_param(property, 0)[0]=="PCB_FOOTPRINT"):
			f_prop = build_kicad_field(property, component_xy, comp_orientation)
			#print str(f_prop)
			if (f_prop!=None):
				f_data.append(f_prop)

	# F 3 "Data Link"
	f_data.append({'ref': '""',  'posx':component_x, 'posy':component_y, 'attributs':'0001'})

	# F 4 and up
	for property in properties:
		if (extract_edif_str_param(property, 0)[0]!="VALUE"):
#			f_prop = build_kicad_field(property, prop_xy, comp_orientation)
			f_prop = build_kicad_field(property, component_xy, comp_orientation)
			if (f_prop!=None):
				f_data.append(f_prop)

	#print value + " " + f1_data['attributs']

	#*******
	for field in f_data:
		kicad_component.add_field(field)

	return kicad_component




def extract_kicad_wires(edif_net):

	wires = []
	figures = search_edif_objects(edif_net, "figure")
	for figure in figures:
		if (figure!=None):
			if (figure.get_param(0) == "WIRE"):
				pts = figure.get_object("path.pointList")
				for i in range(0, pts.get_nb_param()):
					pt = pts.get_param(i)
					x, y = convert_kicad_coor( extract_edif_pt(pt) )
					if (i>0):
						wire = KicadWire(xn, yn, x, y)
						wires.append( wire )
					xn, yn = [x, y]

	if (len(wires)==0):
		return None
	else:
		return wires


def extract_kicad_net_aliases(edif_net):
	net_aliases = []
	net_name = extract_edif_str_param(edif_net, 0)
	if (net_name!=None):
		if (type(net_name[0])!=unicode):
			display_list = search_edif_objects(net_name[0], "display" )
			for display in display_list:
				pt = display.get_object("origin.pt")
				if (pt!=None):
					x, y = convert_kicad_coor( extract_edif_pt(pt) )
					#print net_name[1], x, y
					netAlias = KicadNetAlias(x, y, normalize_edif_string(net_name[1]))
					net_aliases.append(netAlias)

	if (len(net_aliases)==0):
		return None
	else:
		return net_aliases


def extract_kicad_junctions(edif_net):
	junctions = []
	instances = search_edif_objects(edif_net, "instance")
	for instance in instances:
		if (instance!=None):
			id = instance.get_param(0)
			pt = instance.get_object("transform.origin.pt")
			if (pt!=None):
				x, y = convert_kicad_coor( extract_edif_pt(pt) )
				junction = KicadJunction( x, y )
				junctions.append(junction)

	if (len(junctions)==0):
		return None
	else:
		return junctions



def extract_kicad_port(edif_port):
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

	viewRef = instance.get_object("viewRef")
	name = viewRef.get_param(0)

	"""
	pt = instance.get_object("transform.origin.pt")
	if (pt!=None):
		component_x, component_y = extract_pt(pt)
	"""
	port_orientation = instance.get_object("transform.orientation")
	if (port_orientation!=None):
		port_orientation = remove_quote(port_orientation.get_param(0))
	else:
		port_orientation = "R0"

	pt = edif_port.get_object("connectLocation.figure.dot.pt")
	if (pt!=None):
		component_x, component_y = convert_kicad_coor( extract_edif_pt(pt) )
	else:
		return
	#print "x, y = " + str([component_x, component_y])
	pI = edif_port.get_param(0)

	if (type(pI)==unicode):
		pI_type = None
		pI_name = pI
		#print "UNICODE: " + str(pI)
	else:

		instance = edif_port.get_object("instance")
		if (instance!=None):
			viewRef = instance.get_object("viewRef")

		pI_type = pI.get_context()
		if (pI_type=="name"):
			# text module
			pI_name = normalize_edif_string(pI.get_param(0))
			#print "pI_name = " + str(pI_name)

			display = pI.get_object("display")
			if (display!=None):
				pI_type = display.get_param(0)
				designator_pt = display.get_object("origin.pt")

				display_orientation = display.get_object("orientation")
				if (display_orientation!=None):
					text_orientation = remove_quote(display_orientation.get_param(0))
				else:
					text_orientation = "R0"
				display_justify = display.get_object("justify")
				if (display_justify!=None):
					hvjustify = text_justify(display_justify.get_param(0), text_orientation, port_orientation)

				display_orientation = display.get_object("orientation")
				if (display_orientation!=None):
					refdes_orientation = remove_quote(display_orientation.get_param(0))
				else:
					refdes_orientation = "R0"

				refdes_orientation = convert_edif_orientation_to_hv(refdes_orientation, port_orientation)

				if (designator_pt!=None):
					porttext_x, porttext_y = convert_kicad_local_coor(extract_edif_pt(designator_pt), [component_x, component_y], port_orientation)
					port_is_labeled = True

					#print "port " + str(pI_name) + " of " + str(pI_type) + " at : " + str(porttext_x) +", " + str(porttext_y)

	if (pI_type=="MODULETEXT"):

		textPort = KicadTextPort(p1_name, component_x, component_y)

		name, rot = name.split("_")
		name = name.replace("PORT", "")

		if (name=="BOTH"):
			port_type = "BiDi"
		elif (name=="LEFT"):
			port_type = "Output"
		elif (name=="RIGHT"):
			port_type = "Input"
		else:
			port_type = "UnSpc"

		if (rot=="L"):
			a = 1
		else:
			a = 0


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
		comb_angle = def_rot[orientation][a]

		#print name, rot, orientation, comb_angle


		textPort.set_text(p2_name[1])
		textPort.set_type(port_type)
		textPort.set_rotation(comb_angle)

		return textPort



	if (pI_type=="POWERTEXT" or (pI_type==None and pI_name in {'GND', 'GNDA', 'GNDD', 'GNDS', 'EARTH', 'GND_POWER'})):
		ref = "\"#PWR?\""
	else:
		ref = "\""+name+"\""

	value = "\""+pI_name+"\""

	#x = component_x
	#y = component_y
	x, y = [porttext_x, porttext_y]

	f0_data = {'ref': ref, 'posx':x, 'posy':y, 'attributs':'0001'}
	if (port_is_labeled==True):
		f1_data = {'ref': value, 'posx':porttext_x, 'posy':porttext_y, 'attributs':'0000', 'orient':refdes_orientation, 'hjust':hvjustify[0],
					'props':hvjustify[1] + "NN"}
	else:
		f1_data = {'ref': value, 'posx':x, 'posy':y, 'attributs':'0001'}

	f2_data = {'ref': '""',  'posx':component_x, 'posy':component_y, 'attributs':'0001'}
	f3_data = {'ref': '""',  'posx':component_x, 'posy':component_y, 'attributs':'0001'}

	kicad_component = KicadSchematicComponent(name, ref)
	kicad_component.set_position(component_x, component_y)
	kicad_component.set_orientation(port_orientation)
	kicad_component.add_field(f0_data)
	kicad_component.add_field(f1_data)
	kicad_component.add_field(f2_data)
	kicad_component.add_field(f3_data)
	return kicad_component
