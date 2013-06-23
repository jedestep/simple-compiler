#Jed Estep
#aje@jhu.edu
#Assignment 5
#600.428

import entry

class Node:
	def __init__(self):
		self.position = None

class Instruction(Node):
	def __init__(self):
		self.nxt = None

class Condition(Node):
	def __init__(self, left, right, rel):
		self.left = left
		self.right = right
		self.rel = rel

class Expression(Node):
	def __init__(self, typ):
		self.typ = typ

class Int(Expression):
	def __init__(self, val):
		Expression.__init__(self, entry.integer_type())
		self.val = val

class Binary(Expression):
	def __init__(self):
		Expression.__init__(self, entry.integer_type())
		self.left = None
		self.right = None
		self.operator = ""

class Location(Expression):
	def __init__(self, typ):
		Expression.__init__(self, typ)

class Var(Location):
	def __init__(self, node):	
		Expression.__init__(self, node.typ)
		self.node = node #a node from the symbol table
		self.name = ""

class Field(Location):
	def __init__(self):
		Expression.__init__(self, None)
		self.location = None
		self.variable = None

class Index(Location):
	def __init__(self, typ):
		Expression.__init__(self, typ)
		self.location = None
		self.expression = None

class Assign(Instruction):
	def __init__(self, location, expression):
		Instruction.__init__(self)
		self.location = location
		self.expression = expression

class Write(Instruction):
	def __init__(self, expression):
		Instruction.__init__(self)
		self.expression = expression

class Read(Instruction):
	def __init__(self, location):
		Instruction.__init__(self)
		self.location = location

class Repeat(Instruction):
	def __init__(self, condition, instructions):
		Instruction.__init__(self)
		self.condition = condition
		self.instructions = instructions

class If(Instruction):
	def __init__(self, condition, i_true, i_false):
		Instruction.__init__(self)
		self.condition = condition
		self.i_true = i_true
		self.i_false = i_false

class FunctionCall(Expression):
	def __init__(self, procedure, arglist, typ):
		Expression.__init__(self, typ)
		self.procedure = procedure
		self.arglist = arglist

class ProcedureCall(Instruction):
	def __init__(self, procedure, arglist):
		Instruction.__init__(self)
		self.procedure = procedure
		self.arglist = arglist
