#Jed Estep
#aje@jhu.edu
#Assignment #1
#600.428

class TokenType:
	EMPTY = -1
	INTEGER = 0
	IDENTIFIER = 1
	KEYWORD = 2
	PUNCTUATION = 3

class Token:
	string_value = ""
	integer_value = 0
	token_type = TokenType.EMPTY
	s_position = 0
	e_position = 0

	def __init__(self, sval, ival, typ, spos, epos):
		self.string_value = sval
		self.integer_value = ival
		self.token_type = typ
		self.s_position = spos
		self.e_position = epos
	
	def __str__(self):
		s = ""
		if(self.token_type == TokenType.EMPTY):
			s += "eof"
		elif(self.token_type == TokenType.INTEGER):
			s += "integer<" + str(self.integer_value) + ">"
		elif(self.token_type == TokenType.IDENTIFIER):
			s += "identifier<" + self.string_value + ">"
		elif(self.token_type == TokenType.KEYWORD):
			s += self.string_value
		elif(self.token_type == TokenType.PUNCTUATION):
			s += self.string_value
		s += "@(" + str(self.s_position) + ", " + str(self.e_position) + ")"
		return s
