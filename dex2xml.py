#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       ******** WORK IN PROGESS!!! ********
#
# Python script to convert DEXonline database to xml format for creating a MOBI dictionary
# Due to Kindle fonts, the diacritics for Romanian language are not displayed properly
# (Romanian standard defines diacritics as letters with comma (,) and Kindle displays these with cedilla)
# Due to this problem, searching for terms containing diacritics with comma would not return any result.
# This was overcome by exporting terms and inflected forms both with comma and with cedilla
#
#
# This script exports a number of HTML files and one OPF
# The OPF file can be converted to MOBI using "mobigen.exe <file>.opf"
# mobigen.exe available at:
#   http://www.mobipocket.com/soft/prcgen/mobigen.zip
#
# Tested with Kindle Paperwhite 2013
#
# BUGS:
# 		..... 
#
# TO DO:
# 		- usage help
# 		- optimize SQL queries
# 		- ....
#
# This python script is based on tab2opf.py by Klokan Petr Přidal (www.klokan.cz)
#
# Requirements:
#		Linux or Wine/Windows enivronment (Windows is needed for mobigen.exe)
#		MySQL server
#		copy of DEXonline database - download and installation instructions: http://wiki.dexonline.ro/wiki/Instruc%C8%9Biuni_de_instalare
#		Python (this script was created and tested using Python 2.7)
#		PyMySql package (compiled from sources or installed using "pip install pymysql")
#		
#
# Version history:
#
# 0.2.1	(17.12.2014) dex2xmls.py - mtz_ro_2003@yahoo.com
#			added parameters for connecting to MySql server
#			added posibility to chose the dictionary sources
#
# 0.2		(16.12.2014) dex2xml.py - mtz_ro_2003@yahoo.com
#			initial dex2xml.py version
#
# 0.1		(19.07.2007) Initial version of tab2opf.py - Copyright (C) 2007 - Klokan Petr Přidal (www.klokan.cz)
#
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
VERSION = "0.2.1"

import sys
import re
import os

from unicodedata import normalize, decomposition, combining
import string
from exceptions import UnicodeEncodeError

import pymysql
import codecs
import getpass

def replacewithcedilla(termen):
	findreplace = [
	(u"\u0218",u"\u015E"),
	(u"\u0219",u"\u015F"),
	(u"\u021A",u"\u0162"),
	(u"\u021B",u"\u0163"),
	]
	for couple in findreplace:
		termen = termen.replace(couple[0],couple[1])
	return termen

def iswithcomma(termen):
	chars = set(u"\u0218\u0219\u021A\u021B")
	if any((c in chars) for c in termen):
		return True
	else:
		return False


def printInflection(termen):
	cur2.execute("SELECT distinct formUtf8General FROM FullTextIndex fti join Definition d on d.id = fti.definitionId join InflectedForm inf on inf.lexemModelId = fti.lexemModelId where fti.position = 0 and d.lexicon = '%s'" % (termen))
	
	if cur2.rowcount>0:
		to.write("""
	            <idx:infl>""")
		for i in range(cur2.rowcount):
			inf = cur2.fetchone()
			inflection = inf["formUtf8General"]
			if inflection:
				to.write("""
                    <idx:iform value="%s"/>""" % (inflection))
				if iswithcomma(inflection): # if the inflected form contains comma it will export the same form written with cedilla
					to.write("""
                    <idx:iform value="%s"/>""" % (replacewithcedilla(inflection)))
		to.write("""
		          </idx:infl>""")
	
	
def printTerm(termen,definition,source):
	to.write("""      <idx:entry name="word" scriptable="yes">
        <h2>
          <idx:orth>%s""" % (termen))
	printInflection(termen)
	to.write("""
            </idx:orth><idx:key key="%s">
        </h2>
        %s
        <br><br>
        <b>Sursa: <i>%s</i></b>
      </idx:entry>
      <mbp:pagebreak/>
""" % (termen, definition,source))

	if iswithcomma(termen):	# if the term contains comma it will export again the same term (and inflected forms), but written with cedilla
		termcedilla = replacewithcedilla(termen)
		to.write("""      <idx:entry name="word" scriptable="yes">
        <h2>
          <idx:orth>%s""" % (termcedilla))
		printInflection(termen)
		to.write("""
            </idx:orth><idx:key key="%s">
        </h2>
        %s
        <br><br>
        <b>Sursa: <i>%s</i></b>
      </idx:entry>
      <mbp:pagebreak/>
""" % (termcedilla, definition,source))

OPFTEMPLATEHEAD1 = """<?xml version="1.0"?><!DOCTYPE package SYSTEM "oeb1.ent">

<!-- the command line instruction 'prcgen dictionary.opf' will produce the dictionary.prc file in the same folder-->
<!-- the command line instruction 'mobigen dictionary.opf' will produce the dictionary.mobi file in the same folder-->

<package unique-identifier="uid" xmlns:dc="Dublin Core">

<metadata>
	<dc-metadata>
		<dc:Identifier id="uid">%s</dc:Identifier>
		<!-- Title of the document -->
		<dc:Title><h2>%s</h2></dc:Title>
		<dc:Language>RO</dc:Language>
	</dc-metadata>
	<x-metadata>
"""
OPFTEMPLATEHEADNOUTF = """		<output encoding="UTF-8" flatten-dynamic-dir="yes"/>"""
OPFTEMPLATEHEAD2 = """
		<DictionaryInLanguage>ro</DictionaryInLanguage>
		<DictionaryOutLanguage>ro</DictionaryOutLanguage>
		<meta name="cover" content="Coperta" />
	</x-metadata>
</metadata>

<!-- list of all the files needed to produce the .prc file -->
<manifest>
 <item href="cover.jpg" id="Coperta" media-type="image/jpeg" />
"""

OPFTEMPLATELINE = """ <item id="dictionary%d" href="%s%d.html" media-type="text/x-oeb1-document"/>
"""

OPFTEMPLATEMIDDLE = """</manifest>


<!-- list of the html files in the correct order  -->
<spine>
"""

OPFTEMPLATELINEREF = """	<itemref idref="dictionary%d"/>
"""

OPFTEMPLATEEND = """</spine>

<tours/>
<guide> <reference type="search" title="Dictionary Search" onclick= "index_search()"/> </guide>
</package>
"""

################################################################
# MAIN
################################################################

mysql_server = raw_input('\nEnter the name/ip of the MySQL server [default: %s]: ' % 'localhost') or 'localhost'
print("Using '%s'" % mysql_server)

mysql_port = raw_input('\nEnter the port for the server [default: %s]: ' % 3306) or 3306
print("Using '%s'" % mysql_port)

mysql_user = raw_input('\nEnter the username for the MySQL server [default: %s]: ' % 'root') or 'root'
print("Using '%s'" % mysql_user)

mysql_passwd = getpass.getpass('\nEnter the password for the user %s: ' % mysql_user)
print("Using '%s'" % ('*' * len(mysql_passwd)))

mysql_db = raw_input('\nDEXonline database name [default: %s]: ' % 'DEX') or 'DEX'
print("Using '%s'" % mysql_db)

try:
	conn = pymysql.connect(host=mysql_server, port=mysql_port, user=mysql_user, passwd=mysql_passwd, db=mysql_db,charset='utf8')
#except:
except pymysql.OperationalError as e:
	print('\nGot error {!r}, errno is {}'.format(e, e.args[0]))
	print("\nCould not connect to MySQL server using the parameters you entered.\nPlease make sure that the server is running and try again...")
	raw_input("Press any key to exit...")
	sys.exit

cur = conn.cursor(pymysql.cursors.DictCursor)
cur2 = conn.cursor(pymysql.cursors.DictCursor)

name = raw_input("\nEnter the filename of the generated dictionary file.\nMay include path [default: '%s']: " % "DEXonline 2014") or "DEXonline 2014"
print("Using '%s'" % name)

source_list = ["27","28","29","31","32","33","36"]

cur.execute("select id,concat(name,' ',year) as source from source where id in (%s) order by id" % ','.join(source_list))

print("\nCurrent sources of dictionaries for export:\n")

for i in range(cur.rowcount):
	src = cur.fetchone()
	print("%s\n" % src["source"].encode("utf-8"))

response = raw_input("Do you want to change the default sources list [y/N]: ").lower()
if (response == 'y') or (response == 'yes'):
	source_list = []
	cur.execute("select id,concat(name,' ',year) as source from source order by id")
	print("Current source of definitions %s" % cur.rowcount)
	for i in range(cur.rowcount):
		src = cur.fetchone()
		response = raw_input('\nUse as a source (%s of %s) %s [y/N]? ' % (i+1,cur.rowcount-1,src["source"].encode("utf-8"))).lower()
		if (response == 'y') or (response == 'yes'):
			source_list.append(str(src["id"]))
	print source_list
	print("\nSelected sources of dictionaries for export:\n")
	cur.execute("select id,concat(name,' ',year) as source from source where id in (%s) order by id" % ','.join(source_list))
	for i in range(cur.rowcount):
		src = cur.fetchone()
		print("%s\n" % src["source"].encode("utf-8"))
	cur.close()
	
	response = raw_input("Continue [Y/n]: ").lower()
	if (response == 'n') or (response == 'no'):
		sys.exit()

cur.execute("SELECT lexicon,replace(htmlRep,'\n','') as htmlRep, concat(s.name,' ',s.year) as source from Definition d join Source s on d.sourceId = s.id where s.id in (%s) and lexicon <>'' and status = 0 order by lexicon" % ','.join(source_list))
# If you want different sources you must edit the above SQL query
i = 0
to = codecs.open("%s%d.html" % (name, i / 10000),"w","utf-8")

for i in range(cur.rowcount):
    row = cur.fetchone()
    if i % 10000 == 0:
        if to:
            to.write("""
                </mbp:frameset>
              </body>
            </html>
            """)
            to.close()
        to = codecs.open("%s%d.html" % (name, i / 10000), "w","utf-8")

        to.write("""<?xml version="1.0" encoding="utf-8"?>
<html xmlns:idx="www.mobipocket.com" xmlns:mbp="www.mobipocket.com" xmlns:xlink="http://www.w3.org/1999/xlink">
  <body>
    <mbp:pagebreak/>
    <mbp:frameset>
      <mbp:slave-frame display="bottom" device="all" breadth="auto" leftmargin="0" rightmargin="0" bottommargin="0" topmargin="0">
        <div align="center" bgcolor="yellow"/>
        <a onclick="index_search()">Dictionary Search</a>
        </div>
      </mbp:slave-frame>
      <mbp:pagebreak/>
""")

    dterm = row["lexicon"]
    ddef = row["htmlRep"]
    dsrc = row["source"]
    
    print dterm.encode("utf-8")
    printTerm(dterm,ddef,dsrc)


to.write("""
    </mbp:frameset>
  </body>
</html>
""")
print("\nTotal of %i definitions" % (i+1))
to.close()
cur.close()
cur2.close()
lineno = i

to = open("%s.opf" % name, 'w')
to.write(OPFTEMPLATEHEAD1 % (name, name))
to.write(OPFTEMPLATEHEADNOUTF)
to.write(OPFTEMPLATEHEAD2)
for i in range(0,(lineno/10000)+1):
    to.write(OPFTEMPLATELINE % (i, name, i))
to.write(OPFTEMPLATEMIDDLE)
for i in range(0,(lineno/10000)+1):
    to.write(OPFTEMPLATELINEREF % i)
to.write(OPFTEMPLATEEND)

to.close()
raw_input("\nJob finished, file %s.OPF was generated.\nPress any key..." % name)
