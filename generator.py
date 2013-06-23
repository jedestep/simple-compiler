#Jed Estep
#aje@jhu.edu
#Assignment 6
#600.428

import entry
import astnodes
import sys

class SimpleCompilationError:
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
		self._write("\taddi 1, 1, " + str(self.usage) + " #shrink the stack by the amount we used in total")
		self._write("\tlwz 0, 8(1) #restore link address from under the stack")
		self._write("\tmtlr 0 #move link address to link register")
		self._write("\tblr #return")

	def ast_traverse(self):
		self._prologue()
		self._ast_traverse(self.ast)
		self._epilogue()
	def _ast_traverse(self, curr):
		if isinstance(curr, astnodes.Int):
			self._write("## Push integer ##")
			self._write("\taddi 1, 1, -4 #advance stack head by sizeof(int) = 4")
			self.usage += 4
			self._write("\tlis 30, " + str(curr.val.value) + "@ha #r30 := value; load in halfwords")
			self._write("\taddi 30, 30, " + str(curr.val.value) + "@l #load bottom 16 bits")
			self._write("\tstw 30, 0(1) #push the value onto the stack")
		if isinstance(curr, astnodes.Var):
			self._write("## Push variable address ##")
			self._write("\taddi 1, 1, -4 #advance stack head by sizeof(addr) = 4")
			self.usage += 4
			self._write("\tlis 30, defn@ha #load the top 16 bits of static memory location to r30")
			self._write("\taddi 30, 30, defn@l #load bottom 16 bits")
			self._write("\taddi 30, 30, " + str(curr.node.address) + " #add offset amount")
			self._write("\tstw 30, 0(1) #push the value onto the stack")
		if isinstance(curr, astnodes.Binary):
			self._write("## Binary computation ##")
			self._ast_traverse(curr.right)
			self._ast_traverse(curr.left)
			self._write("# Compute value from binary operator#")
			self._write("\tlwz 30, 0(1) #pop the stack into r30; value left")
			self.usage -= 4
			self._write("\taddi 1, 1, 4 #shrink the stack by 4")
			self._write("\tlwz 29, 0(1) #pop the stack into r29; value right")
			self.usage -= 4
			self._write("\taddi 1, 1, 4 #shrink the stack by 4")
			if isinstance(curr.right, astnodes.Location):
				self._write("\tlwz 29, 0(29) #dereference r29, since it held a pointer")
			if isinstance(curr.left, astnodes.Location):
				self._write("\tlwz 30, 0(30) #dereference r30, since it held a pointer")
			if curr.operator == "+":
				self._write("\tadd 28, 30, 29 #perform addition")
			elif curr.operator == "-":
				self._write("\tsub 28, 30, 29 #perform subtraction")
			elif curr.operator == "*":
				self._write("\tmullw 28, 30, 29 #perform multiplication")
			elif curr.operator == "DIV":
				self._write("\tdivw 28, 30, 29 #perform division")
			elif curr.operator == "MOD":
				self._write("\tdivw 28, 30, 29 #int division for mod")
				self._write("\tmullw 28, 28, 29 #multiplication")
				self._write("\tsub 28, 30, 28 #and subtract for the answer")
			self._write("\taddi 1, 1, -4 #advance stack head by 4")
			self._write("\tstw 28, 0(1) #push the result onto the stack")
			self.usage += 4
		if isinstance(curr, astnodes.Condition):
			self._write("## Condition ##")
			self._ast_traverse(curr.right)
			self._ast_traverse(curr.left)
			self._write("# Perform comparison, store result in cr8 #")
			self._write("\tlwz 30, 0(1) #pop the stack into r30; value left")
			self.usage -= 4
			self._write("\taddi 1, 1, 4 #shrink the stack by 4")
			self._write("\tlwz 29, 0(1) #pop the stack into r29; value right")
			self.usage -= 4
			self._write("\taddi 1, 1, 4 #shrink the stack by 4")
			if isinstance(curr.right, astnodes.Location):
				self._write("\tlwz 29, 0(29) #dereference r29, since it held a pointer")
			if isinstance(curr.left, astnodes.Location):
				self._write("\tlwz 30, 0(30) #dereference r30, since it held a pointer")
			self._write("\tli 20, 0 #prepare constant 0 in r20")
			self._write("\tmtcrf 0xFF, 20 #zero the condition register")
			self._write("\tcmpw 30, 29 #set cr0 to be the comparison result of r30 and r29")
		if isinstance(curr, astnodes.Assign):
			self._write("## Assign a value to a location ##")
			self._ast_traverse(curr.expression)
			self._ast_traverse(curr.location)
			self._write("# Move value into new address #")
			self._write("\tlwz 30, 0(1) #pop the stack into r30; location")
			self.usage -= 4
			self._write("\taddi 1, 1, 4 #shrink the stack by 4")
			self._write("\tmr 29, 1 #get the ADDRESS of the expression into r29")
			self.usage -= 4
			if isinstance(curr.expression, astnodes.Location):
				self._write("\tlwz 29, 0(29) #since the expression was already an address, we want the initial value")
			self._write("\tmr 3, 30 #argument 0 is the target location")
			self._write("\tmr 4, 29 #argument 1 is the source location")
			self._write("\tlis 5, " + str(curr.location.typ.blocksize()) + "@ha #number of bytes to copy")
			self._write("\taddi 5, 5, " + str(curr.location.typ.blocksize()) + "@l #finish loading")
			self._write("\tbl memmove #call C for memmove; easy assigning!")
			self._write("\taddi 1, 1, 4 #shrink the stack by 4; we have to wait so memmove doesn't fail")
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
			self._write("\tlwz 30, 0(1) #pop the stack into r30")
			self.usage -= 4
			self._write("\taddi 1, 1, 4 #shrink the stack by 4")
			self._write("\tlis 3, scanfstr@ha #load format string to r3")
			self._write("\taddi 3, 3, scanfstr@l #finish loading format string")
			self._write("\tmr 4, 30 #place address into r4")
			self._write("\tbl scanf #external call to scanf")
			self._ast_traverse(curr.nxt)
		if isinstance(curr, astnodes.Write):
			self._write("## Write to stdout ##")
			self._write("# Compute expression value to stack #")
			self._ast_traverse(curr.expression)
			self._write("# Perform write #")
			self._write("\tlwz 30, 0(1) #pop the stack into r30")
			self._write("\taddi 1, 1, 4 #shrink the stack by 4")
			self.usage -= 4
			if isinstance(curr.expression, astnodes.Location):
				self._write("\tlwz 30, 0(30) #dereference r30 since it held a pointer")
			self._write("\tlis 3, printfstr@ha #prepare the format string into r3")
			self._write("\taddi 3, 3, printfstr@l #finish loading")
			self._write("\tmr 4, 30 #move value to print into r4")
			self._write("\tcrxor 6,6,6 #most metal instruction ever; necessary for some reason")
			self._write("\tbl printf #branch to printf call")
			self._ast_traverse(curr.nxt)
		if isinstance(curr, astnodes.Index):
			self._write("## Access an array index ##")
			self._write("# Compute index value to stack #")
			self._ast_traverse(curr.expression)
			self._write("# Compute array address to stack #")
			self._ast_traverse(curr.location)
			self._write("# Perform index operation #")
			self._write("\tlwz 30, 0(1) #pop the stack into r30; location")
			self.usage -= 4
			self._write("\taddi 1, 1, 4 #shrink the stack by 4")
			self._write("\tlwz 29, 0(1) #pop the stack into r29; expression")
			self.usage -= 4
			self._write("\taddi 1, 1, 4 #shrink the stack by 4")
			if isinstance(curr.expression, astnodes.Location):
				self._write("\tlwz 29, 0(29) #dereference r29 since it held a pointer")
			self._write("\tli 28, " + str(curr.location.typ.length.value) + " #load the max array length for cmp")
			self._write("\tcmpw 29, 28 #see if the array index is too long")
			self._write("\tbt lt, .IDXN" + str(self.idx_ct) + " #if index in bounds, check negative")
			self._write("\tlis 3, errstr@ha #load error fmt string to r3")
			self._write("\taddi 3, 3, errstr@l #finish loading")
			self._write("\tlis 4, " + str(curr.position) + "@ha #load current position for error reporting")
			self._write("\taddi 4, 4, " + str(curr.position) + "@l #finish loading")
			self._write("\tbl printf #print error string")
			self._write("\taddi 1, 1, " + str(self.usage) + " #fully shrink the stack")
			self._write("\tlwz 0, 8(1) #load stored link register value to r0")
			self._write("\tmtlr 0 #prepare link register")
			self._write("\tblr #return out")
			self._write(".IDXN" + str(self.idx_ct) + ": ")
			self._write("\tli 28, 0 #we check if index is negative next")
			self._write("\tcmpw 29, 28 #perform comparison to 0")
			self._write("\tbf lt, .IDX" + str(self.idx_ct) + " #if index > 0, perform index")		
			self._write("\tlis 3, errstr@ha #load error fmt string to r3")
			self._write("\taddi 3, 3, errstr@l #finish loading")
			self._write("\tlis 4, " + str(curr.position) + "@ha #load current position for error reporting")
			self._write("\taddi 4, 4, " + str(curr.position) + "@l #finish loading")
			self._write("\tbl printf #print error string")
			self._write("\taddi 1, 1, " + str(self.usage) + " #fully shrink the stack")
			self._write("\tlwz 0, 8(1) #load stored link register value to r0")
			self._write("\tmtlr 0 #prepare link register")
			self._write("\tblr #return out")
			self._write(".IDX" + str(self.idx_ct) + ": ")
			self._write("\tmuli 29, 29, " + str(curr.location.typ.typ.blocksize()) + " #multiply the index number by sizeof(elem) to get the proper offset")
			self._write("\tadd 28, 30, 29 #r28 := base address + offset")
			self._write("\taddi 1, 1, -4 #grow the stack by 4")
			self.usage += 4
			self._write("\tstw 28, 0(1) #push the address onto the stack")
			self.idx_ct += 1
		if isinstance(curr, astnodes.Field):
			self._write("## Access a record field ##")
			self._write("# Compute record address to stack #")
			self._ast_traverse(curr.location)
			self._write("# Perform field access #")
			self._write("\tlwz 30, 0(1) #pop the stack into r30")
			self.usage -= 4
			self._write("\taddi 1, 1, 4 #shrink the stack by 4")
			self._write("\tlis 29, " + str(curr.variable.node.address) + "@ha #load rel address of target to 29")
			self._write("\taddi 29, 29, " + str(curr.variable.node.address) + "@l #finish loading")
			self._write("\tadd 28, 29, 30 #r28 := base address + offset")
			self._write("\taddi 1, 1, -4 #grow the stack by 4")
			self.usage += 4
			self._write("\tstw 28, 0(1) #push the address onto the stack")
