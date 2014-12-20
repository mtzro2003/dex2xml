#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# DEX2XML
# =======
# 
# dex2xml is aPython script to convert DEXonline database to xml format for creating a MOBI dictionary.
# 
# Due to Kindle fonts, the diacritics for Romanian language are not displayed properly
# (Romanian standard defines diacritics as letters with comma (,) and Kindle displays these with cedilla)
# Due to this problem, searching for terms containing diacritics with comma would not return any result.
# This was overcome by exporting terms and inflected forms both with comma and with cedilla.
# 
# Tested with Kindle Paperwhite 2013
# 
# This python script is based on tab2opf.py by Klokan Petr Pøidal (www.klokan.cz)
# 
# Requirements:
# -------------
# * Linux or Windows enivronment
# * MySQL server
# * copy of DEXonline database - download and installation instructions: http://wiki.dexonline.ro/wiki/Instruc%C8%9Biuni_de_instalare
# * Python (this script was created and tested using Python 2.7)
# * PyMySql package (compiled from sources or installed using "pip install pymysql")
# 
# optional:
# * kindlegen for generating MOBI format (available for Linux/Windows/Mac at http://www.amazon.com/gp/feature.html?docId=1000765211)
# 
# Version history:
# ----------------
#     0.9.0
#         added full interactive mode
#         added full batch mode
#         added usage help
# 
#     0.2.2
#         various bugfixes and improvements
#         added posibility to directly run 'kindlegen' to convert the OPF to MOBI
# 
#     0.2.1
#         added parameters for connecting to MySql server
#         added posibility to chose the dictionary sources
# 
#     0.2
#         initial dex2xml.py version
# 
#     0.1
#         initial version of tab2opf.py - Copyright (C) 2007 - Klokan Petr Pøidal (www.klokan.cz)
# 
# License
# -------
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Library General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
# 
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.
# 
# You should have received a copy of the GNU Library General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

# VERSION
VERSION = "0.9.0"

import sys
import re
import os
import time
import errno
import glob

from unicodedata import normalize, decomposition, combining
import string
from exceptions import UnicodeEncodeError

import pymysql
import codecs
import getpass
import subprocess
import argparse
from argparse import RawTextHelpFormatter

source_list = ["27","28","29","31","32","33","36"]

mysql_server = ''
mysql_port = ''
mysql_user = ''
mysql_passwd = ''
mysql_db = ''
name = ''
conn =''
cur = ''
cur2 = ''
to = ''

OPFTEMPLATEHEAD = """<?xml version="1.0" encoding="utf-8"?>
<package unique-identifier="uid">
	<metadata>
		<dc-metadata xmlns:dc="http://purl.org/metadata/dublin_core" xmlns:oebpackage="http://openebook.org/namespaces/oeb-package/1.0/">
			<dc:Identifier id="uid">%s</dc:Identifier>
			<!-- Title of the document -->
			<dc:Title><h2>%s</h2></dc:Title>
			<dc:Language>ro</dc:Language>
			<dc:Creator>dex2xml</dc:Creator>
			<dc:Description>DEX online</dc:Description>
			<dc:Date>%s</dc:Date>
	</dc-metadata>
	<x-metadata>
			<output encoding="utf-8" content-type="text/x-oeb1-document"></output>
			<!-- That's how it's recognized as a dictionary: -->
			<DictionaryInLanguage>ro</DictionaryInLanguage>
			<DictionaryOutLanguage>ro</DictionaryOutLanguage>
			<DefaultLookupIndex>word</DefaultLookupIndex>
		</x-metadata>
	</metadata>
	<manifest>
		<item id="cimage" media-type="image/jpeg" href="cover.jpg" properties="cover-image"/>
		<item id="toc" properties="nav" href="%s.xhtml" mediatype="application/xhtml+xml"/>
		<item id="abbr" href="Abrevieri.html" mediatype="text/html"/>
		<!-- list of all the files needed to produce the .prc file -->
"""

OPFTEMPLATEMIDDLE = """	</manifest>
	<spine>
		<itemref idref="cimage"/>
		<itemref idref="toc"/>
		<itemref idref="abbr"/>
		<!-- list of the html files in the correct order  -->
"""

OPFTEMPLATEEND = """	</spine>
	<guide>
		<reference type="toc" title="Table of Contents" href="%s.xhtml"/>
	</guide>
</package>
"""

TOCTEMPLATEHEAD = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="en"
	lang="ro">
	<head>
		<title>DEXonline - Table of Contens</title>
	</head>
	<body>
		<h4 style="text-align:center">Index</h4>
		<hr>
			<nav epub:type="toc" id="toc">
					<ol>
						<li><a href="Abrevieri.html">Abrevieri</a></li>"""

TOCTEMPLATEEND = """
					</ol>
			</nav>
	</body>
</html>
"""

FRAMESETTEMPLATEHEAD = """<html xmlns:math="http://exslt.org/math" xmlns:svg="http://www.w3.org/2000/svg" xmlns:tl="http://www.kreutzfeldt.de/tl" xmlns:saxon="http://saxon.sf.net/" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:cx="http://www.kreutzfeldt.de/mmc/cx" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:mbp="http://www.kreutzfeldt.de/mmc/mbp" xmlns:mmc="http://www.kreutzfeldt.de/mmc/mmc" xmlns:idx="http://www.mobipocket.com/idx">
	<head>
		<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
	</head>
	<body>
		<mbp:frameset>"""

FRAMESETTEMPLATEEND = """
		</mbp:frameset>
	</body>
</html>
"""

IDXTEMPLATEHEAD = """
			<idx:entry name="word" scriptable="yes">
				<h2>
					<idx:orth>%s"""

IDXTEMPLATEEND = """
					 </idx:orth>
				</h2>
				%s
				<br><br>
				<hr>
				<h6>Sursa: <i>%s</i></h6>
			</idx:entry>
			<mbp:pagebreak/>"""

IDXINFTEMPLATEHEAD = """
						<idx:infl>"""

IDXINFTEMPLATEEND = """
						 </idx:infl>"""

IDXINFVALUETEMPLATE = """
								<idx:iform value="%s" exact="yes" />"""


def replaceWithCedilla(termen):
	findreplace = [
	(u"\u0218",u"\u015E"),
	(u"\u0219",u"\u015F"),
	(u"\u021A",u"\u0162"),
	(u"\u021B",u"\u0163"),
	]
	for couple in findreplace:
		termen = termen.replace(couple[0],couple[1])
	return termen


def isWithComma(termen):
	chars = set(u"\u0218\u0219\u021A\u021B")
	if any((c in chars) for c in termen):
		return True
	else:
		return False


def printInflection(termen):
	global to
	
	to.write(IDXINFVALUETEMPLATE % termen)

def printInflections(iddef):
	global to
	global cur2
	
	to.write(IDXINFTEMPLATEHEAD)
	
	cur2.execute("select distinct formUtf8General from Definition d join LexemDefinitionMap ldm on ldm.definitionid = d.id join LexemModel lm on lm.lexemid = ldm.lexemId join InflectedForm inf on inf.lexemModelId = lm.id where d.id = %s" % iddef)
	
	if cur2.rowcount>0:
		for i in range(cur2.rowcount):
			inf = cur2.fetchone()
			inflection = inf["formUtf8General"]
			if inflection:
				printInflection(replaceWithCedilla(inflection))
				# if the inflected form contains comma it will export the same form written with cedilla
				if isWithComma(inflection):
					printInflection(replaceWithCedilla(inflection))


	to.write(IDXINFTEMPLATEEND)

def printTerm(iddef,termen,definition,source):
	global to
	
	to.write(IDXTEMPLATEHEAD % (termen))
	printInflections(iddef)
	to.write(IDXTEMPLATEEND % (definition,source))

def deleteFile(filename):
	try:
			os.remove(filename)
	except OSError as e:
		if e.errno != errno.ENOENT:	# errno.ENOENT = no such file or directory
			raise 										# re-raise exception if a different error occured

def deleteFiles(filemask,mobi):
	for fl in glob.glob(u'' + filemask + u'*.html'):
		deleteFile(fl)
	deleteFile(filemask + '_TOC.xhtml')
	deleteFile(filemask + '.opf')
	if mobi:
		deleteFile(filemask + '.mobi')

def deleteTemporaryFiles():
	response = 'n'
	if args.interactive:
		response = raw_input("\nDo you want to delete the temporary files (%s*.html and %s.opf) [Y/n]?: " % (name,name)).lower() or 'y'
	if (args.interactive) or (args.temp_files) or ((response == 'y') or (response == 'yes')):
		deleteFiles(name, mobi = False)
		print("Done removing files.")

def tryConnect():
	global mysql_server
	global mysql_port
	global mysql_user
	global mysql_passwd
	global mysql_db
	global conn
	global cur
	global cur2

	try:
		conn = pymysql.connect(host=mysql_server, port=mysql_port, user=mysql_user, passwd=mysql_passwd, db=mysql_db,charset='utf8')
	except pymysql.OperationalError as e:
		print('\nGot error {!r}, errno is {}'.format(e, e.args[0]))
		print("\nCould not connect to MySQL server using the parameters you entered.\nPlease make sure that the server is running and try again...")
		sys.exit()
	cur = conn.cursor(pymysql.cursors.DictCursor)
	cur2 = conn.cursor(pymysql.cursors.DictCursor)


def exportDictionaryFiles():
	global to
	global cur
	
	start_time = time.time()
	cur.execute("select d.id,lexicon,replace(htmlRep,'\n','') as htmlRep, concat(s.name,' ',s.year) as source from Definition d join Source s on d.sourceId = s.id where s.id in (%s) and lexicon <>'' and status = 0 order by lexicon" % ','.join(source_list))
	
	if cur.rowcount == 0:
		print("Managed to retrieve 0 definitions from dictionary...\nSomething was wrong...")
		sys.exit()
	
	manifest = ''
	spine = ''
	letter = ''
	toc = ''
	to = False
	
	for i in range(cur.rowcount):
		row = cur.fetchone()
	
		did = row["id"]
		dterm = row["lexicon"]
		ddef = row["htmlRep"]
		dsrc = row["source"]
		
		if letter != dterm[0].upper():
			letter = dterm[0].upper()
			if to:
				to.write(FRAMESETTEMPLATEEND)
				to.close()
			filename = name + '_' + letter + '.html'
			if os.path.isfile(filename):
				to = codecs.open(filename, "a","utf-8")
			else:
				to = codecs.open(filename, "w","utf-8")
				to.write(FRAMESETTEMPLATEHEAD)
				manifest = manifest + '\t\t<item id="' + letter + '" href="' + to.name + '" media-type="text/x-oeb1-document"/>\n'
				spine = spine + '\t\t<itemref idref="' + letter + '"/>\n'
				toc = toc + '\n\t\t\t\t\t\t<li><a href="' + to.name + '">' + letter + '</a></li>'
		sys.stdout.write("\rExporting %s of %s..." % (i+1,cur.rowcount))
		
		printTerm(did,dterm,ddef,dsrc)
		#if the term contains comma it will export the term again but written with cedilla
		if isWithComma(dterm):
			printTerm(did,replaceWithCedilla(dterm),ddef,dsrc)
	
	end_time = time.time()
	print("\nExport time: %s" % time.strftime('%H:%M:%S',time.gmtime((end_time - start_time))))
	
	if to:
		to.write(FRAMESETTEMPLATEEND)
	
	if to:
			to.close()
	cur.close()
	cur2.close()
	
	to = codecs.open("%s.opf" % name, "w","utf-8")
	to.write(OPFTEMPLATEHEAD % (name, name, time.strftime("%d/%m/%Y"),name + '_TOC'))
	to.write(manifest)
	to.write(OPFTEMPLATEMIDDLE)
	to.write(spine)
	to.write(OPFTEMPLATEEND % (name + '_TOC'))
	to.close()
	
	to = codecs.open("%s_TOC.xhtml" % name, "w","utf-8")
	to.write(TOCTEMPLATEHEAD)
	to.write(toc)
	to.write(TOCTEMPLATEEND)
	to.close()

def runKindlegen():
	start_time = time.time()
#	returncode = subprocess.call(['kindlegen',name + '.opf','-verbose','-dont_append_source','-c2'])
	returncode = subprocess.call(['kindlegen',name + '.opf','-verbose','-dont_append_source'])
	end_time = time.time()
	if returncode < 0:
		print("\nKindlegen failed with return code %s.\nTemporary files will not be deleted..." % returncode)
		return False
	else:
		print("\nKindlegen finished in %s" % time.strftime('%H:%M:%S',time.gmtime((end_time - start_time))))
		return True

def kindlegen():
	response = 'n'
	try:
		subprocess.call(['kindlegen'], stdout=subprocess.PIPE)
	except OSError, e:
		if e.errno == errno.ENOENT:
			print('Kindlegen was not on your path; not generating .MOBI version...')
			print('You can download kindlegen for Linux/Windows/Mac from http://www.amazon.com/gp/feature.html?docId=1000765211')
			print('and then run: <kindlegen "%s.opf"> to convert the file to MOBI format.' % name)
		else:
			raise
	
	if args.interactive:
		response = raw_input("\nKindlegen was found in your path.\nDo you want to launch it to convert the OPF to MOBI? [Y/n]: ") or 'y'
	if (args.kindlegen) or ((response == 'y') or (response == 'yes')):
		if runKindlegen():
				deleteTemporaryFiles()

def printSources():
	global cur
	global source_list
	
	cur.execute("select id,concat(name,' ',year) as source from Source where id in (%s) order by id" % ','.join(source_list))
	print("\nSources of dictionaries for export:\n")
	
	for i in range(cur.rowcount):
		src = cur.fetchone()
		print("%s" % src["source"].encode("utf-8"))

def interactiveMode():
	global mysql_server
	global mysql_port
	global mysql_user
	global mysql_passwd
	global mysql_db
	global name
	global source_list
	global to 
	
	mysql_server = raw_input('Enter the name/ip of the MySQL server [default: %s]: ' % 'localhost') or 'localhost'
	print("Using '%s'" % mysql_server)
	
	mysql_port = raw_input('Enter the port for the server [default: %s]: ' % 3306) or 3306
	print("Using '%s'" % mysql_port)
	
	mysql_user = raw_input('Enter the username for the MySQL server [default: %s]: ' % 'root') or 'root'
	print("Using '%s'" % mysql_user)
	
	mysql_passwd = getpass.getpass('Enter the password for the user %s: ' % mysql_user)
	print("Using '%s'" % ('*' * len(mysql_passwd)))
	
	mysql_db = raw_input('DEXonline database name [default: %s]: ' % 'DEX') or 'DEX'
	print("Using '%s'" % mysql_db)
	
	name = raw_input("\nEnter the filename of the generated dictionary file.\nExisting files will be deleted.\nMay include path [default: '%s']: " % "DEXonline") or "DEXonline"
	print("Using '%s'" % name)
	
	tryConnect()
	
	printSources()
	
	response = raw_input("\nDo you want to change the default sources list ? [y/N]: ").lower()
	if (response == 'y') or (response == 'yes'):
		source_list = []
		cur.execute("select id,concat(name,' ',year) as source from source order by id")
		for i in range(cur.rowcount):
			src = cur.fetchone()
			response = raw_input('\nUse as a source (%s of %s) %s ? [y/N]: ' % (i+1,cur.rowcount-1,src["source"].encode("utf-8"))).lower()
			if (response == 'y') or (response == 'yes'):
				source_list.append(str(src["id"]))
		print(source_list)
		print("\nSelected sources of dictionaries for export:\n")
		cur.execute("select id,concat(name,' ',year) as source from source where id in (%s) order by id" % ','.join(source_list))
		for i in range(cur.rowcount):
			src = cur.fetchone()
			print("%s\n" % src["source"].encode("utf-8"))
		cur.close()
		
		response = raw_input("Continue [Y/n]: ").lower()
		if (response == 'n') or (response == 'no'):
			sys.exit()
	print

################################################################
# MAIN
################################################################

parser = argparse.ArgumentParser(add_help=False,formatter_class=RawTextHelpFormatter)
group = parser.add_mutually_exclusive_group()
group.add_argument("-i","--interactive",help="run the program in interactive mode",action="store_true")
group.add_argument("-b","--batch",help="run the program in batch mode, taking parameters from command line",action="store_true")
group.add_argument("-h","--help",help="print this help file",action="help")
group.add_argument("-v","--version",help="print the program's version",action="version",version='%(prog)s ' + VERSION)

batchgroup = parser.add_argument_group("Batch arguments")
batchgroup.add_argument("-s","--server",help="Specify the mysql server to connect to.\nDefault: 'localhost'",type=str,default="localhost")
batchgroup.add_argument("-p","--port",help="Mysql server port.\nDefault: 3306",type=int,default=3306)
batchgroup.add_argument("-u","--username",help="Specify the username to connect to mysql server.\nDefault: 'root'",type=str,default="root")
batchgroup.add_argument("-passwd","--password",help="The password of the mysql server.",type=str)
batchgroup.add_argument("-d","--database",help="DEX database on the mysql server.\nDefault 'DEX'",type=str,default="DEX")
batchgroup.add_argument("-src","--sources",help="List of dictionary sources to extract from database.\nMust contain the sources id's from the table 'sources'.\nDefault: 27 28 29 31 32 33 36",nargs='+',type=str)
batchgroup.add_argument("-o","--outputfile",help="Filename of output file.\May include path.\Existing files will be deleted first.\nDefault 'DEXonline'",type=str,default="DEXonline")

batchgroup2 = parser.add_mutually_exclusive_group()
batchgroup2.add_argument("-k","--kindlegen",help="Run kindlegen to convert the output to MOBI.\nDefault set",action="store_false",default=True)
batchgroup2.add_argument("-t","--temp_files",help="Delete the temporary files after running kindlegen.\nDefault set",action="store_false",default=True)

if not len(sys.argv) > 1:
	print("To display help, run '%s -h'" % (sys.argv[0]))
	sys.exit()

args = parser.parse_args()

if args.interactive:
	interactiveMode()
else:
	mysql_server = args.server
	mysql_port = args.port
	mysql_user = args.username
	mysql_passwd = args.password
	mysql_db = args.database
	name = args.outputfile
	if not args.temp_files:
		print("\nWill not remove temporary files after a (successful) conversion with kindlegen...")
	if not args.kindlegen:
		print("\nWill not automatically try to run kindlegen after exporting the dictionary.\nTemporary files will be preserved...")
		args.temp_files = False
	
	tryConnect()
	print("\nSuccessfully connected to database '%s' on '%s:%d', using username '%s' and password '%s'..." % (mysql_db,mysql_server,mysql_port,mysql_user,'*' * len(mysql_passwd)))
	if args.sources:
		source_list = args.sources
		printSources()

deleteFiles(name, mobi = True)
exportDictionaryFiles()
kindlegen()

if args.interactive:
	raw_input("\nPress any key to exit...")
