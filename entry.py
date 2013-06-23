#Jed Estep
#aje@jhu.edu
#Assignment 5
#600.428

import box

class DefinitionError(Exception):
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)

class Entry:
	def __str__(self):
		return "ENTRY"
	def get_box(self):
		pass
	def blocksize(self):
		pass

class Constant(Entry):
	def __init__(self, typ, val):
		self.value = val
		self.typ = typ
	def __str__(self):
		return "CONSTANT " + str(self.value) + " " + str(self.typ)
	def get_box(self):
		b = box.IntegerBox()
		b.setv(self.value)
		return b
	def blocksize(self):
		return 4	

class Variable(Entry):
	def __init__(self, typ):
		self.typ = typ
		self.address = 0
	def __str__(self):
		return "VAR " + str(self.typ)
	def get_box(self):
		return self.typ.get_box()
	def blocksize(self):
		return self.typ.blocksize()

class GlobalVariable(Variable):
	pass
class LocalVariable(Variable):
	pass
class FormalVariable(Variable):
	def __init__(self, typ, argnum):
		Variable.__init__(self, typ)
		self.argnum = argnum
	def get_box(self):
		return box.FormalBox()

class Procedure(Entry):
	def __init__(self):
		self.typ = None
		self.scope = None
		self.body = None
		self.ret = None
	def get_box(self):
		#TODO
		pass

class Type(Entry):
	def __str__(self):
		return "TYPE"

class InvalidType(Entry):
	def __str__(self):
		return "INVALIDTYPE"

class IntegerType(Type):
	def __init__(self):
		self.typ = self
	def __str__(self):
		return "INTEGERTYPE"
	def get_box(self):
		return box.IntegerBox()
	def blocksize(self):
		return 4

#the singleton for the integer type
_INTEGER_TYPE = IntegerType()

def integer_type():
	return _INTEGER_TYPE


class Array(Type):
	def __init__(self, etype, length):
		self.length = length
		self.typ = etype
	def __str__(self):
		return "ARRAYTYPE " + str(self.length) + " " + str(self.etype)
	def get_box(self):
		b = box.ArrayBox()
		for i in xrange(0,self.length.value):
			b.arr.append(self.typ.get_box())
		return b
	def blocksize(self):
		return self.typ.blocksize() * self.length.value

class Record(Type):
	def __init__(self, scope):
		self.scope = scope
	def __str__(self):
		return "RECORDTYPE " + str(self.scope)
	def get_box(self):
		b = box.RecordBox()
		for k, v in self.scope.table.iteritems():
			b.record[k] = v.get_box()
		return b
	def blocksize(self):
		sz = 0
		for k,v in self.scope.table.iteritems():
			sz += v.blocksize()
		return sz


class Scope:
	def __init__(self, outer):
		self.outer = outer
		self.table = {}

	def insert(self, name, value):
		if not self.local(name): #no conflicts, but we allow shadowing variables defined in higher scopes
			self.table[name] = value
		else:
			raise DefinitionError("error: a duplicate definition was found for " + name)

	def find(self, name):
		if self.local(name):
			return self.table[name]
		else:
			if self.outer == None: #this is the universe scope
				raise DefinitionError("error: the symbol " + name + " is not defined")
			else:
				return self.outer.find(name)

	def local(self, name):
		return self.table.has_key(name) #since the result is false whether or not an outer scope contains the definition, we don't even check
