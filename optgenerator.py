#Jed Estep
#aje@jhu.edu
#Assignment 7
#600.428

import entry
import astnodes
import sys

class SimpleCompilationError:
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)

class CompilerContextError:
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)

class Generator:
	def __init__(self, ast, st):
		self.ast = ast
		self.st = st
		self.addr = 0
		self.usage = 0
		self.unused_regs = range(9,32)
		self.inuse_regs = []
		self.item_stack = []
		self.rassoc = {}
		self.if_ct = 0
		self.rpt_ct = 0
		self.idx_ct = 0
		self.out = ""
	def generate(self):
		self.assign_addresses()
		if self.addr >= sys.maxint: #use maxint since we cause an integer overflow trying to dereference a number more than this
			raise SimpleCompilationError("too much memory was requested by this program")
		self.ast_traverse()
	def _write(self, s):
		self.out += s + "\n"
	def assign_addresses(self):
		self.addr = self._assign_addresses(self.st, 0)
	def _assign_addresses(self, curr, addr):
		if isinstance(curr, entry.Variable):
			if isinstance(curr.typ, entry.Record):
				curr.address = addr
				addr += self._assign_addresses(curr.typ.scope, 0)
			else:
				curr.address = addr
				addr += curr.blocksize()
		elif isinstance(curr, entry.Scope):
			a = 0
			for k,v in curr.table.iteritems():
				a = self._assign_addresses(v, addr)
				addr = a
		return addr

	def _prologue(self):
		self._write("## Memory allocation ##")
		self._write(".data")
		self._write("printfstr: .string \"%d\\n\"")
		self._write("scanfstr: .string \"%d\"")
		self._write("errstr: .string \"error: array index out of bounds at token %d\\n\"")
		self._write("defn: .space " + str(self.addr))
		self._write("## Program main section ##")
		self._write(".text")
		self._write(".globl main")
		self._write(".align 2")
		self._write("main:")
		self._write("## Prologue ##")
		self._write("\teieio #and on this farm...")
		self._write("\tmflr 0 #store link register in r0")
		self._write("\tstw 0, 8(1) #push link register onto stack")
	def _epilogue(self):
		self._write("## Epilogue ##")
		self._write("\taddi 1, 1, " + str(self.usage) + " #fully shrink the stack")
		self._write("\tlwz 0, 8(1) #load stored link register value to r0")
		self._write("\tmtlr 0 #prepare link register")
		self._write("\tblr #return")
		self._write("\t.ERROR: #array indexing error")
		self._write("\tlis 3, errstr@ha #load error fmt string to r3")
		self._write("\taddi 3, 3, errstr@l #finish loading")
		self._write("\tbl printf #print error string")
		self._write("\tblr #return out")
	def _next_reg(self,node):
		if self.unused_regs == []:
			self._spill_reg()
		reg = self.unused_regs.pop()
		self.inuse_regs.append(reg)
		self.rassoc[node] = str(reg)
		return str(reg)
	def _spill_reg(self):
		reg = str(self.inuse_regs.pop(0))
		node = None
		for k,v in self.rassoc.iteritems():
			if v == reg:
				node = k
		del self.rassoc[node]
		self._write("\taddi 1, 1, -4 #grow the stack by 4")
		self._write("\tstw " + reg + ", 0(1) #push the value onto the stack")
		self.usage += 4
		self.unused_regs.append(int(reg))
	def _retrieve_reg(self,node):
		if node in self.rassoc:
			return self.rassoc[node]
		else:
			self._write("\tlwz 8, 0(1) #pop from the stack; use r2 for temp storage")
			self._write("\taddi 1, 1, 4 #shrink the stack by 4")
			self.usage -= 4
			reg = self._next_reg(node)
			self._write("\tmr " + reg + ", 8 #move into desired register")
			return reg
	def _free_reg(self,node):
		reg = self.rassoc[node]
		self.unused_regs.append(int(reg))
		del self.rassoc[node]
	def _imm_load(self, reg, value):
		#this is only to do load-immediates
		if value < 32768 and value > -32768:
			self._write("\tli " + reg + ", " + str(value) + " #load constant value")
		else:
			self._write("\tlis " + reg + ", " + str(value) + "@ha #load constant in pieces")
			self._write("\taddi " + reg + ", " + reg + ", " + str(value) + "@l #finish loading")
	def _operate(self, op, reg, regl, regr, istr):

		if op == "+":
			self._write("\tadd" + istr + " " + reg + ", " + regl + ", " + regr + " #perform addition")
		elif op == "-":
			self._write("\tsub" + istr + " " + reg + ", " + regl + ", " + regr + " #perform subtraction")
		elif op == "*":
			if istr == "":
				self._write("\tmullw " + reg + ", " + regl + ", " + regr + " #perform multiplication")
			elif istr == "i":
				self._write("\tmulli " + reg + ", " + regl + ", " + regr + " #perform multiplication")
		elif op == "DIV":
			if istr == "i":
				self._imm_load("8", regr)
				self._write("\tdivw " + reg + ", " + regl + ", 8 #perform division")
			else:
				self._write("\tdivw " + reg + ", " + regl + ", " + regr + " #perform division")
		elif op == "MOD":
			if istr == "":
				self._write("\tdivw " + reg + ", " + regl + ", " + regr + " #for mod, do int division")
				self._write("\tmullw " + reg + ", " + reg + ", " + regr + " #re-multiply")
				self._write("\tsub " + reg + ", " + regl + ", " + reg + " #subtract for the answer")
			elif istr == "i":
				self._imm_load("8", regr)
				self._write("\tdivw " + reg + ", " + regl + ", 8  #for mod, do int division")
				self._write("\tmulli " + reg + ", " + reg + ", 8 #re-multiply")
				self._write("\tsubi " + reg + ", " + regl + ", " + reg + " #subtract for the answer")
	def ast_traverse(self):
		self._prologue()
		self._ast_traverse(self.ast)
		self._epilogue()
	def _ast_traverse(self, curr):
		if isinstance(curr, astnodes.Int):
			self._write("## Push integer ##")
			reg = self._next_reg(curr)
			self._imm_load(reg, curr.val.value)
		if isinstance(curr, astnodes.Var):
			self._write("## Push variable address ##")
			reg = self._next_reg(curr)
			self._write("\tlis " + reg + ", defn@ha #load top 16 bits of static memory into register")
			self._write("\taddi " + reg + ", " + reg + ", defn@l #finish loading static mem address")
			self._write("\taddi " + reg + ", " + reg + ", " + str(curr.node.address) + " #add offset")
		if isinstance(curr, astnodes.Binary):
			self._write("## Binary computation ##")
			self._ast_traverse(curr.right)
			self._ast_traverse(curr.left)
			self._write("# Perform the computation #")
			reg = self._next_reg(curr)
			if isinstance(curr.right, astnodes.Int):
				regl = self._retrieve_reg(curr.left)
				if isinstance(curr.left, astnodes.Location):
					self._write("\tlwz " + regl + ", 0(" + regl + ") #dereference regleft")
				self._operate(curr.operator, reg, regl, str(curr.right.val.value), "i")
				self._free_reg(curr.left)
			elif isinstance(curr.left, astnodes.Int):
				regr = self._retrieve_reg(curr.right)
				if isinstance(curr.right, astnodes.Location):
					self._write("\tlwz " + regr + ", 0(" + regr + ") #dereference regleft")
				self._imm_load(reg, curr.left.val.value)
				self._operate(curr.operator, reg, reg, regr, "i")
				self._free_reg(curr.right)
			else:
				regr = self._retrieve_reg(curr.right)
				regl = self._retrieve_reg(curr.left)
				if isinstance(curr.right, astnodes.Location):
					self._write("\tlwz " + regr + ", 0(" + regr + ") #dereference regright")
				if isinstance(curr.left, astnodes.Location):
					self._write("\tlwz " + regl + ", 0(" + regl + ") #dereference regleft")
				self._operate(curr.operator, reg, regl, regr, "")
				self._free_reg(curr.right)
				self._free_reg(curr.left)
		if isinstance(curr, astnodes.Condition):
			self._write("## Condition ##")
			self._ast_traverse(curr.right)
			self._ast_traverse(curr.left)
			regr = self._retrieve_reg(curr.right)
			regl = self._retrieve_reg(curr.left)
			self._write("# Perform comparison, store result in cr8 #")
			if isinstance(curr.right, astnodes.Location):
				self._write("\tlwz " + regr + ", 0(" + regr + ") #dereference reg right")
			if isinstance(curr.left, astnodes.Location):
				self._write("\tlwz " + regl + ", 0(" + regl + ") #dereference reg left")
			self._write("\tcmpw " + regl + ", " + regr + " #set cr0 to be the comparison left and right")
			self._free_reg(curr.right)
			self._free_reg(curr.left)
		if isinstance(curr, astnodes.Assign):
			self._write("## Assign a value to a location ##")
			self._ast_traverse(curr.expression)
			self._ast_traverse(curr.location)
			rege = None
			self._write("# Move to new memory location #")
			if curr.expression in self.rassoc:
				rege = self.rassoc[curr.expression]
				self._write("\taddi 1, 1, -4 #we need the constant to be in memory sadly")
				self._write("\tstw " + rege + ", 0(1) #push it onto the top of the stack")
				self._write("\tmr " + rege + ", 1 #get the address into expression register")
			else:
				regt = self._next_reg(curr.expression)
				self._write("\tmr " + regt + ", 1 #pop ADDRESS from the stack")
				self.usage -= 4
				rege = regt
			regl = self._retrieve_reg(curr.location)
			if isinstance(curr.expression, astnodes.Location):
				self._write("\tlwz " + rege + ", 0(" + rege + ") #dereference expression address")
			self._write("\tmr 3, " + regl + " #argument 0 is the target location")
			self._write("\tmr 4, " + rege + " #argument 1 is the source location")
			self._imm_load("5", curr.location.typ.blocksize())
			self._write("\tbl memmove #call C for memmove; easy assigning!")
			if not curr.expression in self.rassoc:
				self._write("\taddi 1, 1, 4 #shrink the stack by 4")
				pass
			if curr.expression in self.rassoc:
				self._write("\taddi 1, 1, 4 #shrink the stack if we had to use it")
				pass
			self._free_reg(curr.location)
			self._free_reg(curr.expression)
			self._ast_traverse(curr.nxt)
		if isinstance(curr, astnodes.If):
			self._write("## Perform a conditional branch ##")
			self._ast_traverse(curr.condition)
			self._write("# Decide where to move #")
			#here we look at what the condition was actually
			if curr.condition.rel == "<":
				self._write("\tbf lt, .IFF" + str(self.if_ct) + " #if not lessthan, branch away")
			elif curr.condition.rel == ">":
				self._write("\tbf gt, .IFF" + str(self.if_ct) + " #if not morethan, branch away")
			elif curr.condition.rel == "=":
				self._write("\tbf eq, .IFF" + str(self.if_ct) + " #if not equal, branch away")
			elif curr.condition.rel == "#":
				self._write("\tbt eq, .IFF" + str(self.if_ct) + " #if equal, branch away")
			elif curr.condition.rel == "<=":
				self._write("\tbt gt, .IFF" + str(self.if_ct) + " #if morethan, branch away")
			elif curr.condition.rel == ">=":
				self._write("\tbt lt, .IFF" + str(self.if_ct) + " #if lessthan, branch away")
			self._write("# True instructions #")
			self._ast_traverse(curr.i_true)
			self._write("\tb .IFP" + str(self.if_ct))
			self._write("# False instructions #")
			self._write(".IFF" + str(self.if_ct) + ": ")
			self._ast_traverse(curr.i_false)
			self._write("# Post instructions #")
			self._write(".IFP" + str(self.if_ct) + ": ")
			self.if_ct += 1
			self._ast_traverse(curr.nxt)
		if isinstance(curr, astnodes.Repeat):
			self._write("## Repeat a loop ##")
			self._write("# Perform computations and branching #")
			self._write(".RPT" + str(self.rpt_ct) + ": ")
			self._ast_traverse(curr.instructions)
			self._ast_traverse(curr.condition)
			if curr.condition.rel == "<":
				self._write("\tbf lt, .RPT" + str(self.rpt_ct) + " #if not lessthan, repeat")
			elif curr.condition.rel == ">":
				self._write("\tbf gt, .RPT" + str(self.rpt_ct) + " #if not morethan, repeat")
			elif curr.condition.rel == "=":
				self._write("\tbf eq, .RPT" + str(self.rpt_ct) + " #if not equal, repeat")
			elif curr.condition.rel == "#":
				self._write("\tbt eq, .RPT" + str(self.rpt_ct) + " #if equal, repeat")
			elif curr.condition.rel == "<=":
				self._write("\tbt gt, .RPT" + str(self.rpt_ct) + " #if morethan, repeat")
			elif curr.condition.rel == ">=":
				self._write("\tbt lt, .RPT" + str(self.rpt_ct) + " #if lessthan, repeat")
			self.rpt_ct += 1
			self._ast_traverse(curr.nxt)
		if isinstance(curr, astnodes.Read):
			self._write("## Read from stdin ##")
			self._write("# Compute read location to stack #")
			self._ast_traverse(curr.location)
			self._write("# Perform read #")
			regl = self._retrieve_reg(curr.location)
			self._write("\tlis 3, scanfstr@ha #load format string to r3")
			self._write("\taddi 3, 3, scanfstr@l #finish loading format string")
			self._write("\tmr 4, " + regl + " #place address into r4")
			self._write("\tbl scanf #external call to scanf")
			self._free_reg(curr.location)
			self._ast_traverse(curr.nxt)
		if isinstance(curr, astnodes.Write):
			self._write("## Write to stdout ##")
			self._write("# Compute expression value to stack #")
			self._ast_traverse(curr.expression)
			rege = self._retrieve_reg(curr.expression)
			self._write("# Perform write #")
			if isinstance(curr.expression, astnodes.Location):
				self._write("\tlwz " + rege + ", 0(" + rege + ") #dereference expression reg")
			self._write("\tlis 3, printfstr@ha #prepare the format string into r3")
			self._write("\taddi 3, 3, printfstr@l #finish loading")
			self._write("\tmr 4, " + rege + " #move value to print into r4")
			self._write("\tcrxor 6,6,6 #most metal instruction ever; necessary for some reason")
			self._write("\tbl printf #branch to printf call")
			self._free_reg(curr.expression)
			self._ast_traverse(curr.nxt)
		if isinstance(curr, astnodes.Index):
			self._write("## Access an array index ##")
			self._write("# Compute index value to stack #")
			self._ast_traverse(curr.expression)
			self._write("# Compute array address to stack #")
			self._ast_traverse(curr.location)
			regmax = self._next_reg(curr)
			rega = self._retrieve_reg(curr.location)
			regi = self._retrieve_reg(curr.expression)
			if isinstance(curr.expression, astnodes.Location):
				self._write("\tlwz " + regi + ", 0(" + regi + ") #dereference expression")
			self._write("\tlis " + regmax + ", " + str(curr.location.typ.length.value) + "@ha #load the max array length for cmp")
			self._write("\taddi " + regmax + ", " + regmax + ", " + str(curr.location.typ.length.value) + "@l #finish loading")
			self._write("\tcmpw " + regi + ", " + regmax + " #see if the array index is too long")
			self._write("\tbf lt, .IDXN" + str(self.idx_ct) + " #if index out of bounds, error")
			self._write("\tli " + regmax + ", 0 #we check if index is negative next")
			self._write("\tcmpw " + regi + ", " + regmax + " #perform comparison to 0")
			self._write("\tbf lt, .IDX" + str(self.idx_ct) + " #if index > 0, perform index")		
			self._write(".IDXN" + str(self.idx_ct) + ": ")
			self._imm_load("4", curr.position)
			self._write("\taddi 1, 1, " + str(self.usage) + " #shrink the stack by the amount we used")
			self._write("\tlwz 0, 8(1) #restore link address from under the stack")
			self._write("\tmtlr 0 #move link address to link register")
			self._write("\tb .ERROR #go to error printing")
			self._write(".IDX" + str(self.idx_ct) + ": ")
			self._write("\tmuli " + regi + ", " + regi + ", " + str(curr.location.typ.typ.blocksize()) + " #multiply the index number by sizeof(elem) to get the proper offset")
			self._write("\tadd " + regmax + ", " + rega + ", " + regi + " #reg := base address + offset")
			self._free_reg(curr.expression)
			self._free_reg(curr.location)
			self.idx_ct += 1
		if isinstance(curr, astnodes.Field):
			self._write("## Access a record field ##")
			self._write("# Compute record address to stack #")
			self._ast_traverse(curr.location)
			regl = self._retrieve_reg(curr.location)
			regt = self._next_reg(curr)
			self._write("# Perform field access #")
			self._imm_load(regt, curr.variable.node.address)
			self._write("\tadd " + regt + ", " + regt + ", " + regl + " #reg := address + offset")
			self._free_reg(curr.location)
