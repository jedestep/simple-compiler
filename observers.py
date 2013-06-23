import os

terminals = ["PROGRAM", ";", "BEGIN", "END", ".", "CONST", "=", "TYPE", "VAR", ":", "ARRAY", "OF", "RECORD", "+", "-", "*", "DIV", "MOD", "(", ")", ":=", "IF", "THEN", "ELSE", "REPEAT", "WHILE", "UNTIL", "DO", "#", "<", ">", "<=", ">=", "WRITE", "READ", "[", "]", ","]

class BaseObserver:
	def __init__(self):
		self.output_str = "base observer"
	def update(self, s, depth, par, cur):
		pass
	def output(self):
		print self.output_str

class BasicParseObserver(BaseObserver):
	def __init__(self):
		self.output_str = ""
	def update(self, s, depth, par, cur):
		for i in xrange(0,2*depth):
			self.output_str += " "
		self.output_str += str(s) + "\n"
	def output(self):
		print self.output_str

class DOTParseObserver(BaseObserver):
	def __init__(self):
		self.output_str = "strict digraph CST {\n"
	def update(self, st, depth, par, cur):
		s = str(st)
		if "@" in s:
			s = s[:s.index("@")]
		self.output_str += "L" + str(cur) + " [label=\"" + s + "\", shape="
		if s in terminals:
			self.output_str += "diamond]\n"
		else:
			self.output_str += "box]\n"
		if not cur == par:
			self.output_str += "L" + str(par) + " -> L" + str(cur) + "\n"
	def output(self):
		print self.output_str + "}"
