#Jed Estep
#aje@jhu.edu
#Assignment #1
#600.428

import token
import sys

special_chars = {"+","-","*",":","=",";","#","<",">",",",".","[","]","(",")"}
keywords = {"PROGRAM", "BEGIN", "END", "CONST", "TYPE", "VAR", "ARRAY", "OF", "RECORD", "END", "DIV", "MOD", "IF", "THEN", "ELSE", "REPEAT", "UNTIL", "WHILE", "DO", "END", "WRITE", "READ", "PROCEDURE", "RETURN", "PROTOTYPE"}
whitespace = {" ", "\n", "\t", "\r", "\0", "\f"}

class ScanError(Exception):
	def __init__(self, value, lst):
		self.value = value
		self.lst = lst
	def __str__(self):
		return repr(self.value)

class Scanner:
	source_text = ""
	error_msg = ""
	position = 0
	length = 0

	def __init__(self, src):
		self.source_text = src
		self.length = len(src) 
		self.position = 0

	def next(self):
		if self.position >= self.length-1: #we are at EOF; just keep returning eof tokens now
			return token.Token("eof", 0, token.TokenType.EMPTY, self.position, self.position)
		curr_chr = self.source_text[self.position]

		while curr_chr in whitespace: #ignore whitespace; position ourselves at the beginning of the upcoming token
			if self.position >= self.length-1: #if the file ends with whitespace, don't run over
				return token.Token("eof", 0, token.TokenType.EMPTY, self.position, self.position)
			self.position += 1
			curr_chr = self.source_text[self.position]

		token_start = self.position 

		if curr_chr.isalpha(): #this token is an identifier or keyword
			ts = self.string_valued_token(curr_chr)
			typ = token.TokenType.IDENTIFIER
			if ts in keywords: #keyword token
				typ = token.TokenType.KEYWORD	
			return token.Token(ts, 0, typ, token_start, self.position-1)

		elif curr_chr.isdigit(): #this token is an integer
			ti = self.integer_valued_token(curr_chr)
			return token.Token(ti, int(ti), token.TokenType.INTEGER, token_start, self.position-1)
			
		elif curr_chr in special_chars: #this token is a special character, or a special character pair
			ts = self.special_char_token(curr_chr)
			if not ts == "": #do not make a punctuation token for comments
				return token.Token(ts, 0, token.TokenType.PUNCTUATION, token_start, self.position-1)
			else:
				return self.next()
		else: #unrecognized character; error
			raise Exception("unrecognized character " + curr_chr + " at position " + str(self.position))

	def all(self):
		toklist = []
		try:
			cur_tok = next(self)
		except Exception as e:
			raise ScanError(str(e), toklist)
		toklist.append(cur_tok)
		while not cur_tok.token_type == token.TokenType.EMPTY:
			try:
				cur_tok = next(self)
				toklist.append(cur_tok)
			except Exception as e: #pass up a new ScanError
				raise ScanError(str(e), toklist)
		return toklist
			
	def string_valued_token(self, c):
		s = ""
		while self.position < self.length-1:
			c = self.source_text[self.position]
			if not (c.isdigit() or c.isalpha()): 
				break
			s += c
			self.position += 1
		return s

	def integer_valued_token(self, c):
		s = ""
		while c.isdigit() and self.position < self.length-1:
			s += c
			self.position += 1
			c = self.source_text[self.position]
		return s

	def special_char_token(self, c):
		s = ""
		if self.position < self.length-1: #don't run over!
			if c == ':' or c == '<' or c == '>' : #we are looking for '='
				if self.source_text[self.position+1] == '=':
					s = c + "="
					self.position += 1
				else:
					s = c
			elif c == '(': #we are looking for '*'
				if self.source_text[self.position+1] == '*':
					self.devour_comments()
					return s
				else:
					s = c
			else:
				s = c
		else:
			s = c
		self.position += 1
		return s

	def devour_comments(self):
		curr_chr = self.source_text[self.position]
		while self.position < self.length-1:
			self.position+=1
			curr_chr = self.source_text[self.position]
			#check; did we find a *?
			if curr_chr == "*":
				if self.position+1 < self.length and self.source_text[self.position+1] == ")": 
					#don't run over; found a close comment
					self.position+=2
					return ""
				else: #false alarm; keep going
					pass
			else:
				pass
					
		#after while loop; we have found eof
		#we are throwing an exception here!
		raise Exception("unexpected EOF at " + str(self.position) + "; unterminated comment")
