#Jed Estep
#aje@jhu.edu
#Assignment 5
#600.428

import box
import sys
import astnodes
import entry
import copy

class SimpleRuntimeError(Exception):
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)

class Interpreter:
	def __init__(self, ast, st):
		self.ast = ast
		self.st = st
		self.stack = []
		self.env = {}

	def _operate(self, left, right, operator):
		if operator == "+":
			return left + right
		elif operator == "-":
			return left - right
		elif operator == "*":
			return left * right
		elif operator == "DIV":
			try:
				return left / right
			except ZeroDivisionError:
				raise SimpleRuntimeError("division by zero")
		elif operator == "MOD":
			return left % right

	def _compare(self, left, right, rel):
		if rel == "<":
			return left < right
		elif rel == "<=":
			return left <= right
		elif rel == "=":
			return left == right
		elif rel == "#":
			return not left == right
		elif rel == ">":
			return left > right
		elif rel == ">=":
			return left >= right

	def _dereference(self, b):
		if isinstance(b, box.IntegerBox):
			return b.number
		elif isinstance(b, box.ArrayBox):
			return b.arr
		elif isinstance(b, box.RecordBox):
			return b.record
		elif isinstance(b, box.FormalBox):
			return self._cascade_formals(b)
		else:
			return b
	def _cascade_formals(self, b):
		if isinstance(b, box.FormalBox):
			return self._cascade_formals(b.value)
		else:
			return b

	def run(self):
		self._build_env(self.st)
		self._ast_traverse(self.ast, self.env)

	def _build_env(self, curr):
		if isinstance(curr, entry.Scope):
			for k,v in curr.table.iteritems():
				self.env[k] = self._build_env(v)
		elif isinstance(curr, entry.Entry):
			return curr.get_box()

	def _build_local_env(self, curr, args):
		env = {}
		for k,v in self.env.iteritems():
			env[k] = v
		for vname,var in curr.table.iteritems():
			if isinstance(var, entry.FormalVariable):
				b = box.FormalBox()
				val = args[var.argnum]
				if not isinstance(val, box.IntegerBox):
					b.setv(val)
				else:
					b.setv(copy.deepcopy(val))
				env[vname] = b
			elif isinstance(var, entry.LocalVariable):
				b = box.FormalBox()
				b.setv(var)
				env[vname] = b
		return env

	def _ast_traverse(self, curr, ev):
		if isinstance(curr, astnodes.Int):
			self.stack.append(curr.val.value)
		if isinstance(curr, astnodes.Var):
			self.stack.append(ev[curr.name])
		if isinstance(curr, astnodes.Binary):
			self._ast_traverse(curr.left, ev)
			self._ast_traverse(curr.right, ev)
			rval = self._dereference(self.stack.pop())
			lval = self._dereference(self.stack.pop())
			self.stack.append(self._operate(lval, rval, curr.operator))
		if isinstance(curr, astnodes.Condition):
			self._ast_traverse(curr.left, ev)
			self._ast_traverse(curr.right, ev)
			rval = self._dereference(self.stack.pop())
			lval = self._dereference(self.stack.pop())
			self.stack.append(self._compare(lval, rval, curr.rel))
		if isinstance(curr, astnodes.Write):
			self._ast_traverse(curr.expression, ev)
			val = self._dereference(self.stack.pop())
			sys.stdout.write(str(val) + "\n")
			self._ast_traverse(curr.nxt, ev)
		if isinstance(curr, astnodes.Read):
			self._ast_traverse(curr.location, ev)
			loc = self.stack.pop()
			val = sys.stdin.read()
			try:
				val = int(val)
			except Exception:
				#debug
				print "YOU READ SOMETHING INCORRECT"
				pass
				#TODO
			loc.setv(val)
			self._ast_traverse(curr.nxt, ev)
		if isinstance(curr, astnodes.Assign):
			self._ast_traverse(curr.location, ev)
			self._ast_traverse(curr.expression, ev)
			val = self._dereference(self.stack.pop())
			loc = self.stack.pop()
			loc.setv(val)
			self._ast_traverse(curr.nxt, ev)
		if isinstance(curr, astnodes.If):
			self._ast_traverse(curr.condition, ev)
			b = self.stack.pop()
			if b:
				self._ast_traverse(curr.i_true, ev)
			else:
				self._ast_traverse(curr.i_false, ev)
			self._ast_traverse(curr.nxt, ev)
		if isinstance(curr, astnodes.Repeat):
			flag = False
			while not flag:
				self._ast_traverse(curr.instructions, ev)
				self._ast_traverse(curr.condition, ev)
				flag = self.stack.pop()
			self._ast_traverse(curr.nxt, ev)
		if isinstance(curr, astnodes.Index):
			self._ast_traverse(curr.location, ev)
			self._ast_traverse(curr.expression, ev)
			idx = self._dereference(self.stack.pop())
			loc = self.stack.pop()
			if isinstance(loc, box.FormalBox):
				loc = self._dereference(loc)
			lst = self._dereference(loc)
			if (idx < 0) or (idx >= len(lst)):
				raise SimpleRuntimeError("array index out of bounds: " + str(idx) + " at token " + curr.position)
			self.stack.append(loc.ind(idx))
		if isinstance(curr, astnodes.Field):
			self._ast_traverse(curr.location, ev)
			loc = self.stack.pop()
			self._ast_traverse(curr.variable, self._dereference(loc))
		if isinstance(curr, astnodes.ProcedureCall):
			resolved_args = []
			for a in curr.arglist:
				self._ast_traverse(a, ev)
				resolved_args.append(self.stack.pop())
			localenv = self._build_local_env(curr.procedure.scope, resolved_args)
			self._ast_traverse(curr.procedure.body, localenv)
			self._ast_traverse(curr.nxt, ev)
		if isinstance(curr, astnodes.FunctionCall):
			resolved_args = []
			for a in curr.arglist:
				self._ast_traverse(a, ev)
				resolved_args.append(self.stack.pop())
			localenv = self._build_local_env(curr.procedure.scope, resolved_args)
			self._ast_traverse(curr.procedure.body, localenv)
			self._ast_traverse(curr.procedure.ret, localenv)
			retval = self._dereference(self.stack.pop())
			self.stack.append(retval)
