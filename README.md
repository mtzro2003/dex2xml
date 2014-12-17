

Python script to convert DEXonline database to xml format for creating a MOBI dictionary.
Due to Kindle fonts, the diacritics for Romanian language are not displayed properly
(Romanian standard defines diacritics as letters with comma (,) and Kindle displays these with cedilla)
Due to this problem, searching for terms containing diacritics with comma would not return any result.
This was overcome by exporting terms and inflected forms both with comma and with cedilla.

Tested with Kindle Paperwhite 2013

BUGS:
		..... 

TO DO:
	- usage help
	- optimize SQL queries
	- ....

This python script is based on tab2opf.py by Klokan Petr Pøidal (www.klokan.cz)

Requirements:
		Linux or Windows enivronment
		MySQL server
		copy of DEXonline database - download and installation instructions: http://wiki.dexonline.ro/wiki/Instruc%C8%9Biuni_de_instalare
		Python (this script was created and tested using Python 2.7)
		PyMySql package (compiled from sources or installed using "pip install pymysql")
	optional:
		kindlegen for generating MOBI format (available for Linux/Windows/Mac at http://www.amazon.com/gp/feature.html?docId=1000765211)

Version history:

0.2.2	(17.12.2014) dex2xml.py
		various bugfixes and improvements
		added posibility to directly run 'kindlegen' to convert the OPF to MOBI

0.2.1	(17.12.2014) dex2xmls.py - mtz_ro_2003
		added parameters for connecting to MySql server
		added posibility to chose the dictionary sources

0.2	(16.12.2014) dex2xml.py - mtz_ro_2003
		initial dex2xml.py version

0.1	(19.07.2007) Initial version of tab2opf.py - Copyright (C) 2007 - Klokan Petr Pøidal (www.klokan.cz)

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Library General Public
License as published by the Free Software Foundation; either
version 2 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Library General Public License for more details.

You should have received a copy of the GNU Library General Public
License along with this library; if not, write to the
Free Software Foundation, Inc., 59 Temple Place - Suite 330,
Boston, MA 02111-1307, USA.


