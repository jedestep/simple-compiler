#Jed Estep
#aje@jhu.edu
#Assignment 5
#600.428

import astnodes
import entry

class Box:
	def __init__(self):
		self.position = None

class IntegerBox(Box):
	def __init__(self):
		self.number = 0
	def getv(self):
		return self.number
	def setv(self, v):
		self.number = v

class ArrayBox(Box):
	def __init__(self):
		self.arr = []
	def getv(self):
		return self.arr
	def ind(self, index):
		return self.arr[index]
	def setv(self, v):
		self.arr = []
		for l in v:
			self.arr.append(_copy(l))

class RecordBox(Box):
	def __init__(self):
		self.record = {}
	def getv(self):
		return self.record
	def setv(self, v):
		self.record = {}
		for k,v1 in v.iteritems():
			self.record[k] = _copy(v1)
	def ind(self, key):
		return self.arr[key]
class FormalBox(Box):
	def __init__(self):
		self.value = None
	def __str__(self):
		return "FormalBox " + repr(self.value)
	def getv(self):
		return self.value
	def setv(self, v):
		self.value = v
def _copy(bx):
	if isinstance(bx, IntegerBox):
		b = IntegerBox()
	elif isinstance(bx, ArrayBox):
		b = ArrayBox()
	elif isinstance(bx, RecordBox):
		b = RecordBox()
	b.setv(bx.getv())
	return b
		
