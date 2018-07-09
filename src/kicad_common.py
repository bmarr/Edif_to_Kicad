#!/usr/bin/env python

import pprint
import re

def remove_quote(string):
	if (string==None):
		return None

	if (string.startswith('"') and string.endswith('"')):
		string = string[1:-1]
	return string

def add_quote(string):
	string = string.replace("\"", "\\\"")
	string = "\""+string+"\""
	return string

def decode_special_char(string):
	with_quote = False

	if string.startswith('"') and string.endswith('"'):
		string = string[1:-1]
		with_quote = True

	result = re.findall(r'%(\d+)%', string)
	if (result!=None):
		for n in result:
			string = string.replace("%"+n+"%", chr(int(n)))

	string = string.replace("\"", "\\\"")

	if (with_quote):
		string = "\""+string+"\""

	return string

# EDIF net names or labels will be prefixed with ampersand if
# the first character is not a letter.
#  &3V3_VDD
#  &+3V3
# also not case sensitive, these are equal:
#  VDD_3V3
#  vdd_3V3
def normalize_edif_string(test_string):

	if (test_string==None):
		output_string = "NULL"

	if (test_string[0]=='&'):
		output_string = test_string[1:]
	else:
		output_string = test_string

	#print "normalize: " + output_string
	return output_string

def text_justify(edif_justify_param, text_orientation, shape_orientation):
	key = edif_justify_param

	# TODO: test all cases (some not yet covered below)
	if (shape_orientation=="R0"):
		if (text_orientation=="R270"):
			key = text_justify_mirror(key, "MY")
	elif (shape_orientation=="R90"):
		if (text_orientation in {'R0', 'R180'}):
			key = text_justify_mirror(key, "MX")
			key = text_justify_mirror(key, "MY")
	elif (shape_orientation=="MYR90"):
		if (text_orientation in {'R0', 'R180'}):
			key = text_justify_mirror(key, "MY")
	elif (shape_orientation=="MXR90"):
		key = text_justify_mirror(key, "MX")
	else:
		key = text_justify_mirror(key, shape_orientation)

	justify = {
		'UPPERLEFT':['L', 'T'],
		'CENTERLEFT':['L', 'C'],
		'LOWERLEFT':['L', 'B'],
		'UPPERRIGHT':['R', 'T'],
		'CENTERRIGHT':['R', 'C'],
		'LOWERRIGHT':['R', 'B'],
		'UPPERCENTER':['C', 'T'],
		'CENTERCENTER':['C', 'C'],
		'LOWERCENTER':['C', 'B']
		}

	return justify.get(key, 'CENTERCENTER')


def text_justify_mirror(edif_justify_param, orientation):
	key = edif_justify_param

	if (orientation=="MY"):
		translate = {
			'UPPERLEFT':'UPPERRIGHT',
			'LOWERLEFT':'LOWERRIGHT',
			'UPPERRIGHT':'UPPERLEFT',
			'LOWERRIGHT':'LOWERLEFT',
			'CENTERLEFT':'CENTERRIGHT',
			'CENTERRIGHT':'CENTERLEFT'
		}
		key = translate.get(edif_justify_param, 'UPPERLEFT')
	elif (orientation=="MX"):
		translate = {
			'UPPERLEFT':'LOWERLEFT',
			'LOWERLEFT':'UPPERLEFT',
			'UPPERRIGHT':'LOWERRIGHT',
			'LOWERRIGHT':'UPPERRIGHT',
			'UPPERCENTER':'LOWERCENTER',
			'LOWERCENTER':'UPPERCENTER'
		}
		key = translate.get(edif_justify_param, 'UPPERLEFT')

	return key

