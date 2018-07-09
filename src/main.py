#!/usr/bin/env python

import os
import argparse
import sys



from edif_parse_sch import *
from edif_parse_lib import *


global_import_origin = {'origin':"",'version':""}
global_import_views_as_components = False

def configure_import_style_by_origin(origin="unknown", version="unknown"):
	style_was_affected = True
	
	if (origin=="unknown"):
		global_import_views_as_components = False
		style_was_affected = False
	elif (origin=="OrCAD Capture"):
		global_import_views_as_components = True
	else:
		style_was_affected = False
		
	return style_was_affected
	
def parse_status_for_import_origin(parent_edif_object, output_path=".", project_name="TestTemplate"):	
	import_data_origin = "unknown"
	import_data_version = "unknown"

	status_list = search_edif_objects(parent_edif_object, "status")	
	for status_item in status_list:
		if status_item!=None:
			#written_list = search_edif_objects(status, "written")
			#for written_item in written_list:
				#if written_item!=None:
			written = status_item.get_object("written")
			if written!=None:
				dataorigin = written.get_object("dataOrigin")
				if dataorigin!=None:
					import_data_origin = dataorigin.get_param(0)
					if import_data_origin!='""':
						version = dataorigin.get_object("version")
						if version!=None:
							import_data_version = version.get_param(0)
						else:
							import_data_version = "missing"
				
	return {'origin':import_data_origin, 'version':import_data_version}

def kicad_append(kicad_list, kicad_object):
	if (kicad_object!=None):
		kicad_list.append(kicad_object)	

		
def parse_libraries(parent_edif_object, output_path=".", project_name="TestTemplate"):	

	libraries = search_edif_objects(parent_edif_object, "library")	
	kicad_library = Kicad_Library(output_path+"/"+project_name+"-cache")

	if libraries!=None:
		for edif_library in libraries:
			extract_kicad_library(kicad_library, edif_library)
	
	kicad_library.save()

	return kicad_library

	
#def parse_schematic(parent_edif_object, pin_connections, filename, project_name="TestTemplate"):
def parse_schematic(parent_edif_object, filename, project_name="TestTemplate"):
			
			
	schematic = Kicad_Schematic(filename, project_name)			
			
		
	edif_instances = search_edif_objects(parent_edif_object, "instance")
	edif_nets = search_edif_objects(parent_edif_object, "net")
	edif_ports = search_edif_objects(parent_edif_object, "portImplementation")
	edif_annotations = search_edif_objects(parent_edif_object, "annotate")
		
	kicad_components = []
		#kicad_noconnections = []
		
	for instance in edif_instances:
		kicad_append(kicad_components, extract_kicad_component(instance))
		#kicad_append(kicad_noconnections, extract_kicad_noconnection(instance, cache_library))

	
	kicad_wires_list = []
	kicad_net_aliases_list = []
	kicad_junctions_list = []
	for edif_net in edif_nets:
		kicad_append(kicad_wires_list, extract_kicad_wires(edif_net))
	
		kicad_append(kicad_net_aliases_list, extract_kicad_net_aliases(edif_net))
		
		kicad_append(kicad_junctions_list, extract_kicad_junctions(edif_net))
		
	kicad_ports = []
	for edif_port in edif_ports:
		kicad_append(kicad_ports, extract_kicad_port(edif_port) )
		
	kicad_text_notes = []
	for edif_annotation in edif_annotations:
		kicad_append(kicad_text_notes, extract_kicad_text_notes(edif_annotation) )

	
	schematic.add_kicad_object( kicad_components )
	#schematic.add_kicad_object( kicad_noconnections )		
	schematic.add_kicad_object( kicad_ports )		
	schematic.add_kicad_object( kicad_wires_list )
	schematic.add_kicad_object( kicad_net_aliases_list )
	schematic.add_kicad_object( kicad_junctions_list )	
	schematic.add_kicad_object( kicad_text_notes )	
	
	schematic.save()
		
	return schematic



if __name__ == "__main__": 

	parser = argparse.ArgumentParser()
	parser.add_argument('input')	
	args = parser.parse_args()
	
	filename  = args.input
	
	path = os.path.dirname(filename)
	project_name = os.path.basename(filename).split('.')[0]
	
	output_path = path+"/kicad_"+project_name+"/"
	
	print "output path =", output_path
	print "project name = ", project_name
	
	if (not os.path.exists(output_path)):
		os.makedirs(output_path)
		

	
	edif_root = Read_Edif_file(filename)
	
	
	edif_object = edif_root.get_object("edif") 
	if (edif_object!=None):
		obj = edif_object.get_object("edifversion")
		version = obj.get_params( [0, 1, 2] )
		if (version!=None):
			if ( (version[0]=='2') and (version[1]=='0') and(version[2]=='0') ):
				print "Edif 2.0.0 checked ;)"

				global_import_origin = parse_status_for_import_origin(edif_object)
				print "Import origin: " + str(global_import_origin['origin']) + " version: " + str(global_import_origin['version'])
				
				custom_import = configure_import_style_by_origin(global_import_origin['origin'], global_import_origin['version'])
			
				parse_libraries(edif_object, output_path, project_name)
					
				print "---------------------------------------------"	
				pages = search_edif_objects(edif_object, "page")
				page_nb = 0
				for page in pages:
					page_nb+=1
					page_names = extract_edif_str_param(page, 0)
					#page_name = page_names[1].replace(' ', '_')
					page_name = page_names[1].replace('\"','')
					#filename = output_path + page_name
					#filename = output_path + project_name + " - " + page_name
					filename = output_path + project_name
					print filename
					parse_schematic(page, filename, project_name)
					

					
	sys.exit(0)
