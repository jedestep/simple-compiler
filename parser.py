#Jed Estep
#aje@jhu.edu
#Assignment 4
#600.428

import token
import scanner
import sys
import observers
import entry
import astnodes

weak_errors = [";", "(", ")", "[", "]"]
opposite_conditions = {"=": "#", "#": "=", "<" : ">=", ">" : "<=", ">=": "<", "<=" : ">"}

class ParserError(Exception):
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)

class Parser:
	def __init__(self, tokens):
		self.tokens = tokens
		if len(self.tokens) == 0: #we couldn't make any tokens because of a lexing error
			raise ParserError("error: parsing can't take place because of an unrecognized character")
		self.current = tokens[0]
		self.position = 0
		self._obs = [] #observer list
		self._obs_ctr = 0 #counts the number of times anything is observed; needed to build the CST
		self._token_mod = 8 #error handling
		self.error_str = "" #error log
		self.curr_scope = None #current scope
		self._universe = None #permanent link to universe
		self.ast = None
		self._ast_tail = None
		self.semantic = False #by default, do not perform semantic analysis
		self.build_ast = False #by default, do not build an ast
		self.scope_str = ""
		self.ast_str = ""

	def attach(self, o):
		if not o in self._obs:
			self._obs.append(o)

	def detach(self, o):
		try:
			self._obs.remove(o)
		except ValueError:
			pass

	def obs(self):
		return self._obs

	def parse(self):
		#create the universe scope scope
		self._build_universe()
		#start parsing
		self._Program(0)
		if self.semantic:
			self._output_scope(self.curr_scope, 0)
		if self.build_ast:
			self._output_ast()
	def parse_noprint(self):
		self._build_universe()
		self._Program(0)
		self._output_scope(self.curr_scope, 0)

	def _scope_print(self, num, s):
		for i in xrange(0,2*num):
			self.scope_str += " "
		self.scope_str += s + "\n"

	def _ast_print(self, num, s):
		for i in xrange(0,2*num):
			self.ast_str += " "
		self.ast_str += s + "\n"

	def _output_scope(self, obj, depth):

		if isinstance(obj, entry.Scope):
			self._scope_print(depth, "SCOPE BEGIN")
			for k in sorted(obj.table.keys()):
				self._scope_print(depth+1, k + " =>")
				self._output_scope(obj.table[k], depth+2)
			self._scope_print(depth, "END SCOPE")

		elif isinstance(obj, entry.Constant):
			self._scope_print(depth, "CONST BEGIN")
			self._scope_print(depth+1, "type:")
			self._output_scope(obj.typ, depth+2)
			self._scope_print(depth+1, "value:")
			self._scope_print(depth+2, str(obj.value)) #since obj.value stores flat integers
			self._scope_print(depth, "END CONST")

		elif isinstance(obj, entry.IntegerType):
			self._scope_print(depth, "INTEGER")

		elif isinstance(obj, entry.Variable):
			self._scope_print(depth, "VAR BEGIN")
			self._scope_print(depth+1, "type:")
			self._output_scope(obj.typ, depth+2)
			self._scope_print(depth, "END VAR")
			
		elif isinstance(obj, entry.Record):
			self._scope_print(depth, "RECORD BEGIN")
			self._output_scope(obj.scope, depth+1) 
			self._scope_print(depth, "END RECORD")

		elif isinstance(obj, entry.Array):
			self._scope_print(depth, "ARRAY BEGIN")
			self._scope_print(depth+1, "type:")
			self._output_scope(obj.typ, depth+2)
			self._scope_print(depth+1, "length:")
			self._scope_print(depth+2, str(obj.length))
			self._scope_print(depth, "END ARRAY")
		
		elif isinstance(obj, entry.Procedure):
			self._scope_print(depth, "PROCEDURE BEGIN")
			self._output_scope(obj.scope, depth+1)
			self._scope_print(depth, "END PROCEDURE")
	def _output_ast(self):
		self._ast_print(0, "instructions =>")
		self._output_instruction(self.ast, 1)
	def _output_instruction(self, inst, depth):
		if isinstance(inst, astnodes.Assign):
			self._ast_print(depth, "Assign:")
			self._ast_print(depth, "location =>")
			self._output_instruction(inst.location, depth+1)
			self._ast_print(depth, "expression =>")
			self._output_instruction(inst.expression, depth+1)
			if not inst.nxt is None:
				self._output_instruction(inst.nxt, depth)
		elif isinstance(inst, astnodes.Write):
			self._ast_print(depth, "Write:")
			self._ast_print(depth, "expression =>")
			self._output_instruction(inst.expression, depth+1)
			if not inst.nxt is None:
				self._output_instruction(inst.nxt, depth)
		elif isinstance(inst, astnodes.Read):
			self._ast_print(depth, "Read:")
			self._ast_print(depth, "location =>")
			self._output_instruction(inst.location, depth+1)
			if not inst.nxt is None:
				self._output_instruction(inst.nxt, depth)
		elif isinstance(inst, astnodes.Repeat):
			self._ast_print(depth, "Repeat:")
			self._ast_print(depth, "condition =>")
			self._output_instruction(inst.condition, depth+1)
			self._ast_print(depth, "instructions =>")
			self._output_instruction(inst.instructions, depth+1)
			if not inst.nxt is None:
				self._output_instruction(inst.nxt, depth)
		elif isinstance(inst, astnodes.If):
			self._ast_print(depth, "If:")
			self._ast_print(depth, "condition =>")
			self._output_instruction(inst.condition, depth+1)
			self._ast_print(depth, "true =>")
			self._output_instruction(inst.i_true, depth+1)
			if not inst.i_false is None:
				self._ast_print(depth, "false =>")
				self._output_instruction(inst.i_false, depth+1)
			if not inst.nxt is None:
				self._output_instruction(inst.nxt, depth)
		elif isinstance(inst, astnodes.Binary):
			self._ast_print(depth, "Binary (" + str(inst.operator) + "):")
			self._ast_print(depth, "left =>")
			self._output_instruction(inst.left, depth+1)
			self._ast_print(depth, "right =>")
			self._output_instruction(inst.right, depth+1)
		elif isinstance(inst, astnodes.Condition):
			self._ast_print(depth, "Condition (" + str(inst.rel) + "):")
			self._ast_print(depth, "left =>")
			self._output_instruction(inst.left, depth+1)
			self._ast_print(depth, "right =>")
			self._output_instruction(inst.right, depth+1)
		elif isinstance(inst, astnodes.Int):
			self._ast_print(depth, "Number:")
			self._ast_print(depth, "value =>")
			self._output_instruction(inst.val, depth+1)
		elif isinstance(inst, astnodes.Var):
			self._ast_print(depth, "Variable:")
			self._ast_print(depth, "variable =>")
			self._output_instruction(inst.node, depth+1)
		elif isinstance(inst, astnodes.Field):
			self._ast_print(depth, "Field:")
			self._ast_print(depth, "location =>")
			self._output_instruction(inst.location, depth+1)
			self._ast_print(depth, "variable =>")
			self._output_instruction(inst.variable, depth+1)
		elif isinstance(inst, astnodes.Index):
			self._ast_print(depth, "Index:")
			self._ast_print(depth, "location =>")
			self._output_instruction(inst.location, depth+1)
			self._ast_print(depth, "expression =>")
			self._output_instruction(inst.expression, depth+1)
		elif isinstance(inst, astnodes.FunctionCall):
			self._ast_print(depth, "FunctionCall:")
			self._ast_print(depth, "type =>")
			self._output_instruction(inst.typ, depth+1)
			self._ast_print(depth, "procedure =>")
			self._output_instruction(inst.procedure, depth+1)
			self._ast_print(depth, "arglist =>")
			for arg in inst.arglist:
				self._output_instruction(arg, depth+1)
		elif isinstance(inst, astnodes.ProcedureCall):
			self._ast_print(depth, "ProcedureCall:")
			self._ast_print(depth, "procedure =>")
			self._output_instruction(inst.procedure, depth+1)
			self._ast_print(depth, "arglist =>")
			for arg in inst.arglist:
				self._output_instruction(arg, depth+1)
		#symbol table hooks
		elif isinstance(inst, entry.Constant):
			self._ast_print(depth, "CONST BEGIN")
			self._ast_print(depth+1, "type:")
			self._output_instruction(inst.typ, depth+2)
			self._ast_print(depth+1, "value:")
			self._ast_print(depth+2, str(inst.value)) #since obj.value stores flat integers
			self._ast_print(depth, "END CONST")
		elif isinstance(inst, entry.IntegerType):
			self._ast_print(depth, "INTEGER")
		elif isinstance(inst, entry.Variable):
			self._ast_print(depth, "VAR BEGIN")
			self._ast_print(depth+1, "type:")
			self._output_instruction(inst.typ, depth+2)
			self._ast_print(depth, "END VAR")
		elif isinstance(inst, entry.Record):
			self._ast_print(depth, "RECORD BEGIN")
			self._output_instruction(inst.scope, depth+1) 
			self._ast_print(depth, "END RECORD")
		elif isinstance(inst, entry.Array):
			self._ast_print(depth, "ARRAY BEGIN")
			self._ast_print(depth+1, "type:")
			self._output_instruction(inst.typ, depth+2)
			self._ast_print(depth+1, "length:")
			self._ast_print(depth+2, str(inst.length.value))
			self._ast_print(depth, "END ARRAY")
		elif isinstance(inst, entry.Scope):
			self._ast_print(depth, "SCOPE BEGIN")
			for k in sorted(inst.table.keys()):
				self._ast_print(depth+1, k + " =>")
				self._output_instruction(inst.table[k], depth+2)
			self._ast_print(depth, "END SCOPE")
		elif isinstance(inst, entry.Procedure):
			self._ast_print(depth, "PROCEDURE BEGIN")
			self._ast_print(depth, "body =>")
			self._output_instruction(inst.body, depth+1)
			self._ast_print(depth, "return =>")
			self._output_instruction(inst.ret, depth+1)
			self._ast_print(depth, "END PROCEDURE")

	def gast(self):
		s = self._gast(self.ast)
		return "digraph ast {\n" + s + "}\n"

	def _gast(self, obj):
		s = ""
		if isinstance(obj, astnodes.Condition):
			s += self._gast(obj.left)
			s += self._gast(obj.right)
			s += str(id(obj)) + " [label=\"" + obj.rel + "\",shape=box]\n"
			s += str(id(obj)) + " -> " + str(id(obj.left)) + " [label=left]\n"
			s += str(id(obj)) + " -> " + str(id(obj.right)) + " [label=right]\n"
		elif isinstance(obj, astnodes.Binary):
			s += self._gast(obj.left)
			s += self._gast(obj.right)
			s += str(id(obj)) + " [label=\"" + obj.operator + "\",shape=box]\n"
			s += str(id(obj)) + " -> " + str(id(obj.left)) + " [label=left]\n"
			s += str(id(obj)) + " -> " + str(id(obj.right)) + " [label=right]\n"
		elif isinstance(obj, astnodes.Int):
			s += str(id(obj)) + " [label=Number,shape=box]\n"
			s += str(id(obj.val)) + " [label=\"" + str(obj.val.value) + "\",shape=diamond]\n"
			s += str(id(obj)) + " -> " + str(id(obj.val)) + " [label=ST]\n"
		elif isinstance(obj, astnodes.Var):
			s += str(id(obj)) + " [label=Variable,shape=box]\n"
			s += str(id(obj.node)) + " [label=\"" + obj.name + "\",shape=circle]\n"
			s += str(id(obj)) + " -> " + str(id(obj.node)) + " [label=ST]\n"
		elif isinstance(obj, astnodes.Field):
			s += self._gast(obj.location)
			s += self._gast(obj.variable)
			s += str(id(obj)) + " [label=Field,shape=box]\n"
			s += str(id(obj)) + " -> " + str(id(obj.location)) + " [label=location]\n"
			s += str(id(obj)) + " -> " + str(id(obj.variable)) + " [label=variable]\n"
		elif isinstance(obj, astnodes.Index):
			s += self._gast(obj.location)
			s += self._gast(obj.expression)
			s += str(id(obj)) + " [label=Index,shape=box]\n"
			s += str(id(obj)) + " -> " + str(id(obj.location)) + " [label=location]\n"
			s += str(id(obj)) + " -> " + str(id(obj.expression)) + " [label=expression]\n"
		elif isinstance(obj, astnodes.Assign):
			s += self._gast(obj.location)
			s += self._gast(obj.expression)
			s += str(id(obj)) + " [label=\":=\",shape=box]\n"
			s += str(id(obj)) + " -> " + str(id(obj.location)) + " [label=location]\n"
			s += str(id(obj)) + " -> " + str(id(obj.expression)) + " [label=expression]\n"
			if not obj.nxt is None:
				s += self._gast(obj.nxt)
				s += str(id(obj)) + " -> " + str(id(obj.nxt)) + " [label=next,rank=same]\n"
		elif isinstance(obj, astnodes.Write):
			s += self._gast(obj.expression)
			s += str(id(obj)) + " [label=Write,shape=box]\n"
			s += str(id(obj)) + " -> " + str(id(obj.expression)) + " [label=expression]\n"
			if not obj.nxt is None:
				s += self._gast(obj.nxt)
				s += str(id(obj)) + " -> " + str(id(obj.nxt)) + " [label=next,rank=same]\n"
		elif isinstance(obj, astnodes.Read):
			s += self._gast(obj.location)
			s += str(id(obj)) + " [label=Read,shape=box]\n"
			s += str(id(obj)) + " -> " + str(id(obj.location)) + " [label=location]\n"
			if not obj.nxt is None:
				s += self._gast(obj.nxt)
				s += str(id(obj)) + " -> " + str(id(obj.nxt)) + " [label=next,rank=same]\n"
		elif isinstance(obj, astnodes.Repeat):
			s += self._gast(obj.condition)
			s += self._gast(obj.instructions)
			s += str(id(obj)) + " [label=Repeat,shape=box]\n"
			s += str(id(obj)) + " -> " + str(id(obj.condition)) + " [label=condition]\n"
			s += str(id(obj)) + " -> " + str(id(obj.instructions)) + " [label=instructions]\n"
			if not obj.nxt is None:
				s += self._gast(obj.nxt)
				s += str(id(obj)) + " -> " + str(id(obj.nxt)) + " [label=next,rank=same]\n"
		elif isinstance(obj, astnodes.If):
			s += self._gast(obj.rel)
			s += self._gast(obj.i_true)
			if not obj.i_false is None:
				s += self._gast(obj.i_false)
			s += str(id(obj)) + " [label=If,shape=bopx]\n"
			s += str(id(obj)) + " -> " + str(id(obj.rel)) + " [label=condition]\n"
			s += str(id(obj)) + " -> " + str(id(obj.i_true)) + " [label=true]\n"
			if not obj.i_false is None:
				s += str(id(obj)) + " -> " + str(id(obj.i_false)) + " [label=false]\n"
			if not obj.nxt is None:
				s += self._gast(obj.nxt)
				s += str(id(obj)) + " -> " + str(id(obj.nxt)) + " [label=next,rank=same]\n"
		return s

	def gsem(self):
		s = self._gsem(self.curr_scope, [])
		return "digraph sym {\n" + s + "}\n"

	def _gsem(self, obj, defined):
		s = ""
		if isinstance(obj, entry.Scope):
			#first define all other things
			for k in obj.table.keys():
				s += self._gsem(obj.table[k], defined)
			s += "subgraph cluster_"+ str(id(obj)) + " {\n"
			for k in sorted(obj.table.keys()):
				s += k + "_" + str(id(obj))
				s += " [label=\"" + k + "\",shape=box,color=white,fontcolor=black]\n"
			s += str(id(obj)) + " [label=\"\",style=invis]\n}\n"
			for k in obj.table.keys():
				s += k + "_" + str(id(obj)) + " -> " + str(id(obj.table[k])) + "\n"
				 
		elif isinstance(obj, entry.Constant):
			s += str(id(obj)) + " [label=\"" + str(obj.value) + "\",shape=diamond]\n"
			s += str(id(obj)) + " -> " + str(id(obj.typ)) + "\n"
			defined.append(id(obj))
		elif isinstance(obj, entry.IntegerType):
			s += str(id(obj)) + " [label=\"Integer\",shape=box,style=rounded]\n"
		elif isinstance(obj, entry.Variable):
			s += self._gsem(obj.typ, defined)
			s += str(id(obj)) + " [label=\"\",shape=circle]\n"
			s += str(id(obj)) + " -> " + str(id(obj.typ)) + "\n"
		elif isinstance(obj, entry.Record):
			if id(obj) not in defined:
				s += self._gsem(obj.scope, defined)
				s += str(id(obj)) + " [label=\"Record\",shape=box,style=rounded]\n"
				s += str(id(obj)) + " -> " + str(id(obj.scope)) + "\n"
				defined.append(id(obj))
		elif isinstance(obj, entry.Array):
			if id(obj) not in defined:
				s += str(id(obj)) + " [label=\"Array\\nlength: " + str(obj.length) + "\",shape=box,style=rounded]\n"
				s += str(id(obj)) + " -> " + str(id(obj.typ)) + "\n"
				defined.append(id(obj))
		return s

	def _build_universe(self):
		if self.semantic:
			universe = entry.Scope(None)
			universe.insert("INTEGER", entry.integer_type())
			self.curr_scope = universe
			self._universe = universe

	def _build_scope(self):
		if self.semantic:
			scope = entry.Scope(self.curr_scope)
			self.curr_scope = scope

	def _pop_scope(self):
		if self.semantic:
			outer = self.curr_scope.outer
			self.curr_scope.outer = None #sever the link; records cannot lookup fields which they do not contain
			self.curr_scope = outer

	def _output(self, s, depth, par):
		if not self._obs == []:
			for o in self._obs:
				o.update(s, depth, par, self._obs_ctr)
			self._obs_ctr+=1

	def _report_error(self, msg):
		if self._token_mod >= 8:
			self.error_str += msg + "\n"
		self._token_mod = 0

	def _match(self, tokenset, depth, par):
		#tokenset contains strings, not token objects
		for tok in tokenset:
			if tok == self.current.string_value:
				ret = self.current
				self._output(ret, depth, par)
				self._advance()
				return ret
		#if we got this far, we didn't match. error time
		err_msg = "error: expected a token from the set { "
		for tok in tokenset:
			err_msg += tok + " "
		err_msg += "} starting at token " + str(self.position) + " but found " + self.current.string_value
		if not self.current.string_value in weak_errors:
			raise ParserError(err_msg)
		else:
			self._report_error(err_msg)

	def _advance(self):
		if self.position < len(self.tokens) - 1: #do not run over
			self.position += 1
			self.current = self.tokens[self.position]
			self._token_mod += 1
		else:
			self._token_mod += 1
			raise ParserError("error: tried to advance parser, but the end of the scan stream was reached")

	def _sync_stream(self, tokens):
		try:
			while not self.current.string_value in tokens:
				self._advance()
		except ParserError:
			return

	def _add_ast(self, ast):
		if self.ast is None:
			self.ast = ast
			self._ast_tail = ast
		else:
			self._ast_tail.nxt = ast
			self._ast_tail = ast

	def _foldable(self, left, right):
		lconst = False
		rconst = False
		if isinstance(left, astnodes.Int):
			lconst = isinstance(left.val, entry.Constant)
		else:
			lconst = isinstance(left, entry.Constant)
		if isinstance(right, astnodes.Int):
			rconst = isinstance(right.val, entry.Constant)
		else:
			rconst = isinstance(right, entry.Constant)

		return (lconst and rconst)
	def _is_integer(self, obj):
		i = False
		if isinstance(obj, astnodes.Var):
			i = (obj.node.typ == entry.integer_type())
		elif isinstance(obj, astnodes.Int):
			i = True
		elif isinstance(obj, entry.Constant):
			i = True
		elif isinstance(obj, astnodes.Index):
			i = (obj.typ == entry.integer_type())
		elif isinstance(obj, astnodes.Field):
			i = (obj.typ == entry.integer_type())
		elif isinstance(obj, astnodes.Binary):
			i = True
		elif isinstance(obj, astnodes.FunctionCall):
			i = (obj.typ == entry.integer_type())
		return i
	def _fold(self, left, right, operator):
		l1 = left
		r1 = right
		result = None
		if isinstance(left, astnodes.Int):
			l1 = left.val
		if isinstance(right, astnodes.Int):
			r1 = right.val
		if operator == "+":
			result = l1.value + r1.value
		elif operator == "-":
			result = l1.value - r1.value
		elif operator == "*":
			result = l1.value * r1.value
		elif operator == "DIV":
			try:
				result = l1.value / r1.value
			except ZeroDivisionError:
				self._report_error("error: division by zero at token " + str(self.position))
		elif operator == "MOD":
			result = l1.value % r1.value
		return astnodes.Int(entry.Constant(entry.integer_type(), result))

	def _Program(self, depth):
		pos = self._obs_ctr
		self._build_scope() #make the program scope
		self._output("Program", depth, pos)
		self._match(["PROGRAM"], depth+1, pos)
		begin = self._identifier(depth+1, pos)
		self._match([";"], depth+1, pos)
		self._Declarations(depth+1, pos)
		if self.current.string_value == "BEGIN":
			self._match(["BEGIN"], depth+1, pos)
			self.ast = self._Instructions(depth+1, pos)
		try:
			self._match(["END"], depth+1, pos)
			end = self._identifier(depth+1, pos)
			self._match(["."], depth+1, pos)
			if (not begin == end) and self.semantic:
				self._report_error("error: program start and end identifiers do not match")
		except ParserError as e:
			self._report_error(e.value)
		if not self.current.token_type == token.TokenType.EMPTY:
			self._report_error("error: expected eof but found " + str(self.current))

	def _Declarations(self, depth, par):
		pos = self._obs_ctr
		self._output("Declarations", depth, par)
		#being redundant, but avoiding having to fudge the parse tree
		while self.current.string_value in ["CONST", "TYPE", "VAR", "PROCEDURE", "PROTOTYPE"]:
			try:
				if self.current.string_value == "CONST":
					self._ConstDecl(depth+1, pos)
				elif self.current.string_value == "TYPE":
					self._TypeDecl(depth+1, pos)
				elif self.current.string_value == "VAR":
					self._VarDecl(depth+1, pos)
				elif self.current.string_value == "PROCEDURE":
					self._ProcDecl(depth+1, pos)
				elif self.current.string_value == "PROTOTYPE":
					self._ForwardDecl(depth+1, pos)
			except ParserError as e:
				self._report_error(e.value)
				self._sync_stream(["CONST", "VAR", "TYPE", "BEGIN", "PROCEDURE", "PROTOTYPE"])

	def _ConstDecl(self, depth, par):
		pos = self._obs_ctr
		self._output("ConstDecl", depth, par)
		self._match(["CONST"], depth+1, pos)
		while self.current.token_type == token.TokenType.IDENTIFIER:
			ident = self._identifier(depth+1, pos) #capture the identifier name
			self._match(["="], depth+1, pos)
			value = self._Expression(depth+1, pos)
			if self.build_ast:
				value = value.val
			#context condition: value is a constant
				if not isinstance(value, entry.Constant):
					self._report_error("error: expected a constant value in const declaration at token " + str(self.position))
				
			#attempt to define this constant in current scope
			if self.semantic:
				try:
					self.curr_scope.insert(ident, value)
				except entry.DefinitionError as e: #duplicate definition
					self._report_error(e.value + " when defining the token at " + str(self.position))
			self._match([";"], depth+1, pos)
	
	def _TypeDecl(self, depth, par):
		pos = self._obs_ctr
		self._output("TypeDecl", depth, par)
		self._match(["TYPE"], depth+1, pos)
		while self.current.token_type == token.TokenType.IDENTIFIER:
			ident = self._identifier(depth+1, pos)
			self._match(["="], depth+1, pos)
			typ = self._Type(depth+1, pos)
			if self.semantic:
				try:
					self.curr_scope.insert(ident, typ)
				except entry.DefinitionError as e: #duplicate definition
					self._report_error(e.value + " when defining the token at " + str(self.position))
			self._match([";"], depth+1, pos)

	def _VarDecl(self, depth, par):
		pos = self._obs_ctr
		self._output("VarDecl", depth, par)
		self._match(["VAR"], depth+1, pos)
		ids = []
		typ = None
		while self.current.token_type == token.TokenType.IDENTIFIER:
			ids = self._IdentifierList(depth+1, pos)
			self._match([":"], depth+1, pos)
			typ = self._Type(depth+1, pos)
			if self.semantic:
				try:
					for i in ids:
						self.curr_scope.insert(i, entry.GlobalVariable(typ))
				except entry.DefinitionError as e: #duplicate definition
					self._report_error(e.value + " when defining the token at " + str(self.position))
			self._match([";"], depth+1, pos)
		return (ids, typ)
	def _ProcDecl(self, depth, par):
		pos = self._obs_ctr
		self._output("ProcDecl", depth, par)
		self._match(["PROCEDURE"], depth+1, pos)
		fname = self._identifier(depth+1, pos)
		fobj = None
		forward = False
		try:
			fobj = self.curr_scope.find(fname) #this was forward declared
			temp = self.curr_scope
			self.curr_scope = fobj.scope
			self.curr_scope.outer = temp
			forward = True
		except entry.DefinitionError: 
			fobj = entry.Procedure() #this was not forward declared
			try:
				self.curr_scope.insert(fname, fobj)
			except DefinitionError as e:
				self._report_error(e.value + " at token " + str(self.position))
		self._match(["("], depth+1, pos)
		formals = []
		vdec = False
		argnum = 0
		if self.current.token_type == token.TokenType.IDENTIFIER:
			vdec = True
			formals = self._Formals(depth+1, pos)
			if not forward:
				self._build_scope()
				fobj.scope = self.curr_scope
				for vs, t in formals:
					for v in vs:
						try:
							self.curr_scope.insert(v, entry.FormalVariable(t, argnum))
							argnum += 1
						except entry.DefinitionError as e:
							self._report_error(e.value + " at token " + str(self.position))
			else:
				fm = []
				for vs, t in formals:
					for v in vs:
						fm.append((v, t))
				for ((v1,t1), (v2,t2)) in zip(fm, self.curr_scope.table.iteritems()):
					if not (v1 == v2 and t1 == t2.typ):
						self._report_error("error: argument mismatch between prototype and procedure at " + str(self.position))
		self._match([")"], depth+1, pos)
		hasret = False
		if self.current.string_value == ":":
			hasret = True
			self._match([":"], depth+1, pos)
			typ = self._Type(depth+1, pos)
			if not forward:
				fobj.typ = typ
			if not isinstance(typ, entry.IntegerType):
				self._report_error("error: procedures must return integer if they return at token " + str(self.position))
		if forward:
			if not hasret and not fobj.typ == None:
				self._report_error("error: return type mismatch between prototype and procedure at " + str(self.position))
		self._match([";"], depth+1, pos)
		vardecs = []
		while self.current.string_value == "VAR":
			vdec = True
			self._match(["VAR"], depth+1, pos)
			ids = self._IdentifierList(depth+1, pos)
			self._match([":"], depth+1, pos)
			typ = self._Type(depth+1, pos)
			self._match([";"], depth+1, pos)
			vardecs.append((ids, typ))
		for vs, t in vardecs:
			for v in vs:
				try:
					self.curr_scope.insert(v, entry.LocalVariable(t))
				except entry.DefinitionError as e:
					self._report_error(e.value + " at token " + str(self.position))
		if self.current.string_value == "BEGIN":
			self._match(["BEGIN"], depth+1, pos)
			fobj.body = self._Instructions(depth+1, pos)
		if self.current.string_value == "RETURN":
			self._match(["RETURN"], depth+1, pos)
			fobj.ret = self._Expression(depth+1, pos)
		self._match(["END"], depth+1, pos)
		endname = self._identifier(depth+1, pos)
		if not fname == endname: #context condition violated
			self._report_error("error: procedure start and end name do not match at token " + str(self.position))
		self._match([";"], depth+1, pos)
		if vdec:
			self._pop_scope()

	def _ForwardDecl(self, depth, par):
		pos = self._obs_ctr
		self._output("ForwardDecl", depth, par)
		self._match(["PROTOTYPE"], depth+1, pos)
		fname = self._identifier(depth+1, pos)
		fobj = entry.Procedure()
		try:
			self.curr_scope.insert(fname, fobj)
		except DefinitionError as e:
			self._report_error(e.value + " at token " + str(self.position))
		self._match(["("], depth+1, pos)
		formals = []
		vdec = False
		argnum = 0
		if self.current.token_type == token.TokenType.IDENTIFIER:
			vdec = True
			formals = self._Formals(depth+1, pos)
			self._build_scope()
			fobj.scope = self.curr_scope
			for vs, t in formals:
				for v in vs:
					try:
						self.curr_scope.insert(v, entry.FormalVariable(t, argnum))
						argnum += 1
					except entry.DefinitionError as e:
						self._report_error(e.value + " at token " + str(self.position))
		self._match([")"], depth+1, pos)
		if self.current.string_value == ":":
			self._match([":"], depth+1, pos)
			typ = self._Type(depth+1, pos)
			fobj.typ = typ
			if not isinstance(typ, entry.IntegerType):
				self._report_error("error: procedures must return integer if they return at token " + str(self.position))
		self._match([";"], depth+1, pos)
		if vdec:
			self._pop_scope()

	def _Type(self, depth, par):
		pos = self._obs_ctr
		self._output("Type", depth, par)
		ret_type = None
		if self.current.token_type == token.TokenType.IDENTIFIER:
			ident = self._identifier(depth+1, pos)
			if self.semantic:
				try:
					typ = self.curr_scope.find(ident)
					if isinstance(typ, entry.Type):
						ret_type = typ
					else: #context condition: this must be a type, not something else
						self._report_error("error: expected " + ident + " to be a type at token " + str(self.position))
				except entry.DefinitionError as e:
					self._report_error("error: an undefined type referred by " + ident + " was found at token " + str(self.position))
					ret_type = entry.InvalidType()
			return ret_type
		elif self.current.string_value == "ARRAY":
			self._match(["ARRAY"], depth+1, pos)
			length = self._Expression(depth+1, pos)
			if self.build_ast:
				length = length.val
				if not isinstance(length, entry.Constant):
					self._report_error("error: expected array length to be constant at token " + str(self.position))
			if self.build_ast:
				if length.value <= 0:
					self._report_error("error: array must have a positive length at token " + str(self.position))
			self._match(["OF"], depth+1, pos)
			typ = self._Type(depth+1, pos+1)
			if self.semantic:
				ret_type = entry.Array(typ, length) 
			return ret_type
		elif self.current.string_value == "RECORD":
			self._match(["RECORD"], depth+1, pos)
			self._build_scope()
			while self.current.token_type == token.TokenType.IDENTIFIER:
				ids = self._IdentifierList(depth+1, pos)
				self._match([":"], depth+1, pos)
				typ = self._Type(depth+1, pos+1)
				self._match([";"], depth+1, pos)
				if self.semantic:
					try:
						for i in ids:
							self.curr_scope.insert(i, entry.Variable(typ))
					except entry.DefinitionError as e:
						self._report_error(e.value + " when defining the token at " + str(self.position))
			if self.semantic:
				ret_type = entry.Record(self.curr_scope)
				self._pop_scope()
			self._match(["END"], depth+1, pos)
			return ret_type
		else:
			raise ParserError("error: expected identifier, RECORD, or ARRAY, but found " + str(self.current))

	def _Formals(self, depth, par):
		pos = self._obs_ctr
		self._output("Formals", depth, par)
		formals = []
		formals.append(self._Formal(depth+1, pos))
		while self.current.string_value == ";":
			self._match([";"], depth+1, pos)
			formals.append(self._Formal(depth+1, pos))
		return formals
	
	def _Formal(self, depth, par):
		pos = self._obs_ctr
		self._output("Formal", depth, par)
		vlist = self._IdentifierList(depth+1, pos)
		self._match([":"], depth+1, pos)
		typ = self._Type(depth+1, pos)
		return (vlist, typ)

	def _Instructions(self, depth, par):
		pos = self._obs_ctr
		self._output("Instructions", depth, par)
		head = None
		curr = None
		try:
			inst = self._Instruction(depth+1, pos)
			if self.build_ast:
				head = inst
				curr = inst
		except ParserError as e:
			self._report_error(e.value)
			self._sync_stream(["READ", "WRITE", "IF", "WHILE", "REPEAT"])
			self._Instruction(depth+1, pos)
		try: #these are individually wrapped because the above instruction needs to retry, while this one implicitly retries
			while self.current.string_value == ";":
					self._match([";"], depth+1, pos)
					inst = self._Instruction(depth+1, pos)
					if self.build_ast:
						if not curr is None:
							curr.nxt = inst
							curr = inst
		except ParserError as e:
			self._report_error(e.value)
			self._sync_stream(["READ", "WRITE", "IF", "WHILE", "REPEAT"])
		return head


	def _Instruction(self, depth, par):
		pos = self._obs_ctr
		self._output("Instruction", depth, par)
		inst = None
		if self.current.string_value == "IF":
			inst = self._If(depth+1, pos)
		elif self.current.string_value == "REPEAT":
			inst = self._Repeat(depth+1, pos)
		elif self.current.string_value == "WHILE":
			inst = self._While(depth+1, pos)
		elif self.current.string_value == "READ":
			inst = self._Read(depth+1, pos)
		elif self.current.string_value == "WRITE":
			inst = self._Write(depth+1, pos)
		elif self.current.token_type == token.TokenType.IDENTIFIER:
			proc = None
			try:
				proc = self.curr_scope.find(self.current.string_value)
			except entry.DefinitionError as e:
				self._report_error(e.value + " at token " + str(self.position))
			if isinstance(proc, entry.Procedure):
				if not proc.ret == None:
					self._report_error("error: returning procedure called as instruction at token " + str(self.position))
				inst = self._Call(depth+1, pos, "INSTRUCTION")
			else:
				inst = self._Assign(depth+1, pos)
		return inst

	def _If(self, depth, par):
		pos = self._obs_ctr
		epos = str(self.position)
		self._output("If", depth, par)
		self._match(["IF"], depth+1, pos)
		rel = self._Condition(depth+1, pos)
		self._match(["THEN"], depth+1, pos)
		left = self._Instructions(depth+1, pos)
		right = None
		if self.current.string_value == "ELSE":
			self._match(["ELSE"], depth+1, pos)
			right = self._Instructions(depth+1, pos)
		self._match(["END"], depth+1, pos)
		if self.build_ast:
			node = astnodes.If(rel, left, right)
			node.position = epos
			return node
		return None

	def _Repeat(self, depth, par):
		pos = self._obs_ctr
		epos = str(self.position)
		self._output("Repeat", depth, par)
		self._match(["REPEAT"], depth+1, pos)
		inst = self._Instructions(depth+1, pos)
		self._match(["UNTIL"], depth+1, pos)
		condition = self._Condition(depth+1, pos)
		self._match(["END"], depth+1, pos)
		if self.build_ast:
			node = astnodes.Repeat(condition, inst)
			node.position = epos
			return node
		return None
	
	def _While(self, depth, par):
		pos = self._obs_ctr
		epos = str(self.position)
		self._output("While", depth, par)
		self._match(["WHILE"], depth+1, pos)
		condition = self._Condition(depth+1, pos)
		self._match(["DO"], depth, pos)
		inst = self._Instructions(depth+1, pos)
		self._match(["END"], depth, pos)
		if self.build_ast:
			p1 = astnodes.Condition(condition.left, condition.right, opposite_conditions[condition.rel])
			node = astnodes.If(condition, astnodes.Repeat(p1, inst), None)
			node.position = epos
			return node
		return None

	def _Condition(self, depth, par):
		pos = self._obs_ctr
		epos = str(self.position)
		self._output("Condition", depth, par)
		left = self._Expression(depth+1, pos)
		rel = self._match(["=", "#", "<", ">", "<=", ">="], depth+1, pos).string_value
		right = self._Expression(depth+1, pos)
		if self.build_ast:
			if not (left.typ is entry.integer_type() or right.typ is entry.integer_type()):
				self._report_error("error: only integers can be compared at token " + str(self.position))
			node = astnodes.Condition(left, right, rel)
			node.position = epos
			return node
		return None

	def _Write(self, depth, par):
		pos = self._obs_ctr
		epos = str(self.position)
		self._output("Write", depth, par)
		self._match(["WRITE"], depth+1, pos)
		expression = self._Expression(depth+1, pos)
		if self.build_ast:
			if not expression.typ is entry.integer_type():
				self._report_error("error: non-integer value being written at token " + str(self.position))
			node = astnodes.Write(expression)
			node.position = epos
			return node
		return None
	
	def _Read(self, depth, par):
		pos = self._obs_ctr
		epos = str(self.position)
		self._output("Read", depth, par)
		self._match(["READ"], depth+1, pos)
		loc = self._Designator(depth+1, pos)
		if self.build_ast:
			if not loc.typ is entry.integer_type():
				self._report_error("error: non-integer location being read at token " + str(self.position))
			node = astnodes.Read(loc)
			node.position = epos
			return node
		return None

	def _Assign(self, depth, par):
		pos = self._obs_ctr
		epos = str(self.position)
		self._output("Assign", depth, par)
		location = self._Designator(depth+1, pos)
		if self.build_ast:
			if not isinstance(location, astnodes.Location):
				self._report_error("error: assignment must address a variable at token " + str(self.position))
		self._match([":="], depth+1, pos)
		expression = self._Expression(depth+1, pos)
		if self.build_ast:
			if not location.typ is expression.typ:
				self._report_error("error: type mismatch during assignment at token " + str(self.position))
		if self.build_ast:
			if not location.typ is expression.typ:
				self._report_error("error: type mismatch while assigning at token " + str(self.position))
			node = astnodes.Assign(location, expression)
			node.position = epos
			return node
		return None

	def _Call(self, depth, par, exptype):
		pos = self._obs_ctr
		self._output("Assign", depth, par)
		pname = self._identifier(depth+1, pos)
		proc = None
		try:
			proc = self.curr_scope.find(pname)
		except DefinitionError as e:
			self._report_error(e.value + " at token " + str(self.position))
		self._match(["("], depth+1, pos)
		arglist = []
		if self.current.string_value in ["+", "-", "("] or self.current.token_type == token.TokenType.IDENTIFIER or self.current.token_type == token.TokenType.INTEGER:
			#ensure this is ok
			arglist = self._ExpressionList(depth+1, pos)
		self._match([")"], depth+1, pos)
		if exptype == "EXPRESSION":
			return astnodes.FunctionCall(proc, arglist, proc.typ)
		elif exptype == "INSTRUCTION":
			return astnodes.ProcedureCall(proc, arglist)

	def _IdentifierList(self, depth, par):
		pos = self._obs_ctr
		self._output("IdentifierList", depth, par)
		ids = []
		ids.append(self._identifier(depth+1, pos))
		while self.current.string_value == ",":
			self._match([","], depth+1, pos)
			ids.append(self._identifier(depth+1, pos))
		return ids

	def _ExpressionList(self, depth, par):
		pos = self._obs_ctr
		self._output("ExpressionList", depth, par)
		exps = []
		exps.append(self._Expression(depth+1, pos))
		while self.current.string_value == ",":
			self._match([","], depth+1, pos)
			exps.append(self._Expression(depth+1, pos))
		return exps

	def _identifier(self, depth, par):
		ret = ""
		if self.current.token_type == token.TokenType.IDENTIFIER:
			self._output(str(self.current), depth, par)
			ret = self.current.string_value
			self._advance()
		else:
			self._report_error("error: expected identifier but found " + self.current.string_value + " at token " + str(self.position))
		return ret

	def _Expression(self, depth, par):
		pos = self._obs_ctr
		epos = str(self.position)
		self._output("Expression", depth, par)
		root = None
		unary = None
		right = None
		if self.current.string_value in ["+", "-"]:
			unary = self._match(["+", "-"], depth+1, pos).string_value
		left = self._Term(depth+1, pos)
		while self.current.string_value in ["+","-"]:
			operator = self._match(["+", "-"], depth+1, pos).string_value
			right = self._Term(depth+1, pos)
			if self.build_ast:
				if (not self._is_integer(left)) or (not self._is_integer(right)):
					self._report_error("error: arithmetic can only be performed on integers at token " + str(self.position))
			if self.build_ast:
				
				if self._foldable(left, right):
					root = self._fold(left, right, operator)
				else:
					root = astnodes.Binary()
					root.position = epos
					root.left = left
					root.operator = operator
					root.right = right
				left = root
				
		if right == None:
			root = left
		if not (unary is None):
			#this expression has a unary
			
			temp = astnodes.Binary()
			temp.position = epos
			temp.operator = unary
			temp.left = astnodes.Int(entry.Constant(entry.integer_type(), 0))
			temp.right = root
			root = temp
			if self._foldable(root.left, root.right):
				root = self._fold(root.left, root.right, root.operator)
		return root

	def _Term(self, depth, par):
		pos = self._obs_ctr
		epos = str(self.position)
		self._output("Term", depth, par)
		left = self._Factor(depth+1, pos)
		right = None
		root = None
		while self.current.string_value in ["*", "DIV", "MOD"]:
			operator = self._match(["*", "DIV", "MOD"], depth+1, pos).string_value
			right = self._Factor(depth+1, pos)
			if self.build_ast:
				if self._foldable(left, right):
					root = self._fold(left, right, operator)
				else:
					root = astnodes.Binary()
					root.position = epos
					root.left = left
					root.operator = operator
					root.right = right
				left = root
		if right is None:
			root = left
		return root

	def _Factor(self, depth, par):
		pos = self._obs_ctr
		epos = str(self.position)
		self._output("Factor", depth, par)
		if self.current.token_type == token.TokenType.INTEGER: #integer factor
			ret = None
			if self.build_ast:
				ret = astnodes.Int(entry.Constant(entry.integer_type(), self.current.integer_value))
				ret.position = epos
			self._output(str(self.current), depth+1, par)
			self._advance()
			return ret
		if self.current.token_type == token.TokenType.IDENTIFIER:
			typ = None
			try:
				typ = self.curr_scope.find(self.current.string_value)
			except entry.DefinitionError as e:
				self._report_error(e.value + " at token " + str(self.position))
			if isinstance(typ, entry.Procedure):
				if typ.ret == None:
					self._report_error("error: void procedure called in expression at token " + str(self.position))
				call = self._Call(depth+1, pos, "EXPRESSION")
				return call
			else:
				designator = self._Designator(depth+1, pos)
				if self.build_ast:
					if isinstance(designator, entry.Type):
						self._report_error("error: identifier must denote an integer or variable at token " + str(self.position))
					return designator
			return None
		else: #it wasn't a designator; try for an expression
			self._match(["("], depth+1, pos)
			exp = self._Expression(depth+1, pos)
			self._match([")"], depth+1, pos)
			return exp
		
	def _Designator(self, depth, par):
		pos = self._obs_ctr
		self._output("Designator", depth, par)
		parent = self._identifier(depth+1, pos) #the array or record to be selected
		if isinstance(parent, entry.Type):
			self._report_error("error: identifier must denote an integer or variable at token " + str(self.possition))
		selection = self._Selector(depth+1, pos, parent)
		if self.build_ast:
			if selection is None:
				return parent
			return selection
		return None

	def _Selector(self, depth, par, parent):
		pos = self._obs_ctr
		epos = str(self.position)
		self._output("Selector", depth, par)
		root = None
		selectnode = None
		location = None
		if self.build_ast:
			try:
				selectnode = self.curr_scope.find(parent)
				selectnode.position = epos
				if isinstance(selectnode, entry.Constant):
					selectnode = astnodes.Int(selectnode)
				elif isinstance(selectnode, entry.Variable):
					selectnode = astnodes.Var(selectnode)
					selectnode.name = parent
			except entry.DefinitionError as e:
				self._report_error(e.value)
				selectnode = astnodes.Var(astnodes.Expression(entry.InvalidType))
			location = selectnode
		while self.current.string_value in ["[", "."]:
			if self.current.string_value == "[":
				#array index
				self._match(["["], depth+1, pos)
				exps = self._ExpressionList(depth+1, pos)
				self._match(["]"], depth+1, pos)
				if self.build_ast:
					for exp in exps:
						if not isinstance(location.typ, entry.Array):
							self._report_error("error: expected " + str(selectnode) + " to be an array type at token " + str(self.position))
						if not exp.typ is entry.integer_type():
							self._report_error("error: arrays must be indexed by integers at token " + str(self.position))
						root = astnodes.Index(location.typ.typ)
						root.position = str(self.position)
						root.expression = exp
						root.location = location
						location = root
			if self.current.string_value == ".":
				#record field
				if self.build_ast:
					if not isinstance(location.typ, entry.Record):
						self._report_error("error: expected " + str(selectnode) + " to be a record type at token " + str(self.position))
					rec_scope = location.typ.scope
					root = astnodes.Field()
					root.position = str(self.position)
				self._match(["."], depth+1, pos)
				field_name = self._identifier(depth+1, pos)
				if self.build_ast:
					try:
						variable = rec_scope.find(field_name)
						root.variable = astnodes.Var(variable)
						root.position = str(self.position)
						root.variable.name=field_name
						root.location = location
						root.typ = variable.typ
						location = root
					except entry.DefinitionError:
						self._report_error("error: undefined record field " + field_name + " at token " + str(self.position))
		#location will be None if build_ast is false
		if not root is None:
			return root
		return location
