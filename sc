#!/usr/bin/python

#Jed Estep
#aje@jhu.edu
#Assignment 7
#600.428

import sys
import scanner
import observers
import parser
import interpreter
import generator
import optgenerator

src_str = ""
if sys.argv[1] == "-s":
	if len(sys.argv) > 2:
		try:
			src_str = open(sys.argv[2], 'r').read()
		except IOError as e:
			sys.stderr.write("error: " + str(e))
	else:
		src_str += sys.stdin.read() + "\0" #make sure the string is terminated
		print ""
			
	scn = scanner.Scanner(src_str)
	try:
		tokens = scn.all()
		for t in tokens:
			print t
	except scanner.ScanError as e:
		for t in e.lst:
			print t
		sys.stderr.write("error: " + e.value+"\n")

elif sys.argv[1] in ["-c", "-t", "-a"]:
	g = False
	observer = None
	if len(sys.argv) > 2:
		if sys.argv[2] == "-g":
			src_str = open(sys.argv[3], 'r').read()
			observer = observers.DOTParseObserver()
			g = True
		else:
			src_str = open(sys.argv[2], 'r').read()
			observer = observers.BasicParseObserver()
	else:
		observer = observers.BasicParseObserver()
		src_str += sys.stdin.read() + "\0"
		print ""
	scn = scanner.Scanner(src_str)
	tokens = []
	try:
		tokens = scn.all()
		prs = parser.Parser(tokens)
	except scanner.ScanError as e:
		sys.stderr.write("error: " + e.value + "\n")
		sys.exit(1)
	prs.attach(observer)
	prs.semantic = True
	prs.build_ast = True
	try:
		if sys.argv[1] == "-a":
			prs.parse()
		else:
			prs.parse_noprint()
	except parser.ParserError as e:
		sys.stderr.write(e.value + "\n")
		if prs.error_str == "":
			prs.error_str = " "
	if not prs.error_str == "":
		sys.stderr.write(prs.error_str + "\n")
	else:
		if sys.argv[1] == "-c":
			for o in prs.obs():
				o.output()
		elif sys.argv[1] == "-t":
			if not g:
				print prs.scope_str	
			else:
				print prs.gsem
		elif sys.argv[1] == "-a":
			if not g:
				print prs.ast_str
			else:
				print prs.gast()
elif sys.argv[1] == "-i":
	if len(sys.argv) > 2:
		src_str = open(sys.argv[2], 'r').read()
	else:
		src_str += sys.stdin.read() + "\0"
		print ""
	scn = scanner.Scanner(src_str)
	tokens = []
	try:
		tokens = scn.all()
		prs = parser.Parser(tokens)
	except scanner.ScanError as e:
		sys.stderr.write("error: " + e.value + "\n")
		sys.exit(1)
	prs.attach(observers.BaseObserver())
	prs.semantic = True
	prs.build_ast = True
	try:
		prs.parse_noprint()
	except parser.ParserError as e:
		sys.stderr.write(e.value + "\n")
		if prs.error_str == "":
			prs.error_str = " "
	if not prs.error_str == "":
		sys.stderr.write(prs.error_str + "\n")
	else:
		i = interpreter.Interpreter(prs.ast, prs.curr_scope)
		try:
			i.run()
		except interpreter.SimpleRuntimeError as e:
			sys.stderr.write("error: " + e.value + "\n")
elif sys.argv[1] == "-x":
	if len(sys.argv) > 2:
		src_str = open(sys.argv[2], 'r').read()
	else:
		src_str += sys.stdin.read() + "\0"
		print ""
	scn = scanner.Scanner(src_str)
	tokens = []
	try:
		tokens = scn.all()
		prs = parser.Parser(tokens)
	except scanner.ScanError as e:
		sys.stderr.write("error: " + e.value + "\n")
		sys.exit(1)
	prs.attach(observers.BaseObserver())
	prs.semantic = True
	prs.build_ast = True
	try:
		prs.parse()
	except parser.ParserError as e:
		sys.stderr.write(e.value + "\n")
		if prs.error_str == "":
			prs.error_str = " "
	if not prs.error_str == "":
		sys.stderr.write(prs.error_str + "\n")
	else:
		gen = optgenerator.Generator(prs.ast, prs.curr_scope)
		gen.generate()
		if len(sys.argv) > 2:
			fout = open(sys.argv[2][:sys.argv[2].index(".")] + ".s", 'w')
			fout.write(gen.out)
		else:
			sys.stdout.write(gen.out)
else:
	if len(sys.argv) > 1:
		src_str = open(sys.argv[1], 'r').read()
	else:
		src_str += sys.stdin.read() + "\0"
		print ""
	scn = scanner.Scanner(src_str)
	tokens = []
	try:
		tokens = scn.all()
		prs = parser.Parser(tokens)
	except Scanner.ScanError as e:
		sys.stderr.write("error: " + e.value + "\n")
		sys.exit(1)
	prs.attach(observers.BaseObserver())
	prs.semantic = True
	prs.build_ast = True
	try:
		prs.parse()
	except parser.ParserError as e:
		sys.stderr.write(e.value + "\n")
		if prs.error_str == "":
			prs.error_str = " "
	if not prs.error_str == "":
		sys.stderr.write(prs.error_str + "\n")
	else:
		gen = generator.Generator(prs.ast, prs.curr_scope)
		gen.generate()
		if len(sys.argv) > 1:
			fout = open(sys.argv[1][:sys.argv[1].index(".")] + ".s", 'w')
			fout.write(gen.out)
		else:
			sys.stdout.write(gen.out)	
