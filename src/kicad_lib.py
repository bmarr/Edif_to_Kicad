#!/usr/bin/env python


import math
import numpy as np

from kicad_common import *

def convert_kicad_coor(pt):
	K = 10
	return [pt[0]*K, +pt[1]*K]

class Kicad_Arc(object):

	def __init__(self):
		self.def_field = {'XY_center':{0,0},
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

	def add_point(self, x, y):
		self.arcpoints.append( [x, y])

	def set_offset(self, x, y):
		self.offset = [x, y]

# https://stackoverflow.com/questions/20314306/find-arc-circle-equation-given-three-points-in-space-3d
	def output(self):
		x, y = self.arcpoints[2]
		A = np.array([x, y])		# start point
		x, y = self.arcpoints[1]
		B = np.array([x, y])		# middle point
		x, y = self.arcpoints[0]
		C = np.array([x, y])		# end point

		a = np.linalg.norm(C - B)
		b = np.linalg.norm(C - A)
		c = np.linalg.norm(B - A)
		s = (a + b + c) / 2
		R = a*b*c / 4 / np.sqrt(s * (s - a) * (s - b) * (s - c))
		b1 = a*a * (b*b + c*c - a*a)
		b2 = b*b * (a*a + c*c - b*b)
		b3 = c*c * (a*a + b*b - c*c)
		P = np.column_stack((A, B, C)).dot(np.hstack((b1, b2, b3)))
		P /= b1 + b2 + b3

		#self.def_field['radius'] = str(int(R))
		x, y = P					# center
		self.def_field['XY_center'] = (x, y)
		x, y = A
		self.def_field['XY_arcpoints'].append([x, y]) # start point
		x, y = C
		self.def_field['XY_arcpoints'].append([x, y]) # end point

		to_write = 'A '
		x, y = self.def_field['XY_center']
		#print "*** R = " + str(int(R)) + " P = " + str(x) + ", " + str(y) + " ***"
		to_write += str(int(x))+' '+str(int(y))+' '
		to_write += str( self.def_field['radius'] )+' '
		to_write += str( self.def_field['angle1'] )+' '
		to_write += str( self.def_field['angle2'] )+' '
		to_write += str( self.def_field['unit'] )+' '
		to_write += str( self.def_field['convert'] )+' '
		to_write += str( self.def_field['width'] )+' '
		to_write += str( self.def_field['fill'] )+' '
		for x, y in self.def_field['XY_arcpoints']:
			to_write += str(self.offset[0] + x)+' '+str(self.offset[1] + y)+' '
		to_write += '\n'
		return to_write

class Kicad_Poly(object):

	def __init__(self):
		self.def_field = {'count':0,
				'part':0,
				'dmg':1,
				'pen':10,
				'XY_poly':[],
				'fill':'N'
				}
		self.offset = [0, 0]

	def add_segment(self, x, y):
		self.def_field['XY_poly'].append( [x, y])
		self.def_field['count']+=1

	def set_offset(self, x, y):
		self.offset = [x, y]

	def output(self):
		to_write = 'P '
		to_write += str( self.def_field['count'] )+' '
		to_write += str( self.def_field['part'] )+' '
		to_write += str( self.def_field['dmg'] )+' '
		to_write += str( self.def_field['pen'] )+' '
		for x, y in self.def_field['XY_poly']:
			to_write += str(self.offset[0] + x)+' '+str(self.offset[1] + y)+' '
		to_write += str( self.def_field['fill'] )
		to_write += '\n'
		return to_write


class Kicad_Rectangle(object):

	def __init__(self, x1, y1, x2, y2):
		self.def_field = {'x1':x1, 'y1':y1, 'x2':x2,'y2':y2,
				'part':0,
				'dmg':1,
				'pen':10,
				'fill':'N'
				}
		self.offset = [0, 0]

	def set_offset(self, x, y):
		self.offset = [x, y]

	def output(self):
		to_write = 'S '
		"""
		print self.def_field
		for key in self.def_field:
			print key,"=", self.def_field[key]
		"""
		to_write += str( self.offset[0] + self.def_field['x1'] )+' '
		to_write += str( self.offset[1] + self.def_field['y1'] )+' '
		to_write += str( self.offset[0] + self.def_field['x2'] )+' '
		to_write += str( self.offset[1] + self.def_field['y2'] )+' '
		to_write += str( self.def_field['part'] )+' '
		to_write += str( self.def_field['dmg'] )+' '
		to_write += str( self.def_field['pen'] )+' '
		to_write += self.def_field['fill']+'\n'
		return to_write

class Kicad_Circle(object):

	def __init__(self, x1, y1, x2, y2):
		dx = (x1-x2)
		dy = (y1-y2)
		radius = int(math.sqrt(dx*dx+dy*dy)/2)
		x = x1 - dx/2
		y = y1 - dy/2
		self.def_field = {'x':x, 'y':y, 'radius':radius,
				'part':0,
				'dmg':1,
				'pen':10,
				'fill':'N'
				}
		self.offset = [0, 0]

	def set_offset(self, x, y):
		self.offset = [x, y]

	def output(self):
		to_write = 'C '
		"""
		print self.def_field
		for key in self.def_field:
			print key,"=", self.def_field[key]
		"""
		to_write += str( self.offset[0] + self.def_field['x'] )+' '
		to_write += str( self.offset[1] + self.def_field['y'] )+' '
		to_write += str( self.def_field['radius'] )+' '
		to_write += str( self.def_field['part'] )+' '
		to_write += str( self.def_field['dmg'] )+' '
		to_write += str( self.def_field['pen'] )+' '
		to_write += self.def_field['fill']+'\n'
		return to_write

class Kicad_Connection(object):

	def __init__(self, pin_number, pin_name=''):
		if (pin_number==''):
			pin_number = pin_name
			pin_name = '~'
		#elif (pin_name==''):
		#	pin_name = '~'

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
		#print "pin #" + str(pin_number) + ", name = " + str(pin_name)
	def set_offset(self, x, y):
		self.offset = [x, y]

	def set_direction(self, direction):
		self.direction = direction

	def set_shape(self, shape):
		self.shape = shape

	def set_type(self, type):
		self.type = type

	def set_pin(self, x1, y1, x2, y2):

		dx = x1-x2
		dy = y1-y2

		if ((dx<0) and (dy==0)):
			self.def_field['direction'] = 'R'
		if ((dx>0) and (dy==0)):
			self.def_field['direction'] = 'L'

		if ((dx==0) and (dy>0)):
			self.def_field['direction'] = 'D'
		if ((dx==0) and (dy<0)):
			self.def_field['direction'] = 'U'

		self.def_field['length'] = int(math.sqrt(dx*dx+dy*dy))
		self.def_field['x'] = self.offset[0] + x1
		self.def_field['y'] = self.offset[1] + y1

	def output(self):
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
		to_write += str( self.def_field['dmg'] )+' '
		to_write += str( self.def_field['type'] )+' '
		to_write += self.def_field['shape']
		to_write += '\n'
		return to_write







class Kicad_Library_Component(object):
	_F_KEYS = ['id', 'ref', 'posx', 'posy', 'size', 'text_orientation', 'visible', 'text_align', 'props']

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
		self.ref = ref

	def set_powerobject(self, bool):
		if (bool==True):
			self.powerobject = 'P'

	def set_pin_names_visible(self, bool):
		if (bool==False):
			self.pin_names_visible = 'N'

	def set_pin_numbers_visible(self, bool):
		if (bool==False):
			self.pin_numbers_visible = 'N'

	def addField(self, field_data):
		def_field = {'id':None, 'ref':None,
			'posx':'0',
			'posy':'0',
			'size':'50',
			'text_orientation':'H',
			'visible':'V',
			'text_align':'L',
			'props':'CNN'}

		field = dict(list(def_field.items()) + list(field_data.items()))
		#field['id'] = str(len(self.fields))

		self.fields.append(field)
		return field

	def addDraw(self, draw):
		self.draws.append(draw)

	def addConnection(self, connection):
		self.connections.append(connection)

	def addAlias(self, alias):
		if (alias!=self.name):
			self.alias = alias


	def output(self):

		to_write = []


		try:
			test_field = self.fields[0]['id']
		except IndexError:
			test_field = None


		if ( (test_field==None) or (test_field!=0) ):
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
					self.powerobject + '\n']

		to_write += [ '$FPLIST\n' ]
		to_write += [ '$ENDFPLIST\n' ]

		for field in self.fields:
			line = 'F'
			for key in self._F_KEYS:
				line += str( field[key] ) + ' '
			to_write += [line.rstrip() + '\n']

		if (self.alias!=''):
			to_write += ['ALIAS '+self.alias+'\n']

		to_write += [ 'DRAW\n' ]

		for draw in self.draws:
			#print "==================>",draw.output()
			to_write += [ draw.output() ]

		for connection in self.connections:
			to_write += [ connection.output() ]

		to_write += [ 'ENDDRAW\n' ]

		to_write += ['ENDDEF\n']



		return to_write


class Kicad_Library(object):


	def __init__(self, lib_name):
		self.name = lib_name
		self.__component_list = {}


	def addComponent(self, lib_component):
		comp_name = lib_component.name
		try:
			comp = self.__component_list[comp_name]
		except KeyError:
			self.__component_list[comp_name] = lib_component


	def output(self):
		#pprint.pprint(self.__component_list)
		to_write = []
		for key in self.__component_list:
			to_write += self.__component_list[key].output()
		return to_write

	def save(self, filename=None):

		if not filename:
			filename = self.name+".lib"

		to_write = []

		to_write += "EESchema-LIBRARY Version 2.3\n#encoding utf-8\n"

		to_write += self.output()

		to_write += "#\n#End Library\n"

		f = open(filename, 'w')
		f.writelines(to_write)
		f.close()
