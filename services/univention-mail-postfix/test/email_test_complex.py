#!/usr/bin/python
#
# Univention Mail Postfix
#  mail testing script
#
# Copyright (C) 2004, 2005, 2006 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

# This script does virus and spam checking by sending 4 mails:
#
# - No Spam, Virus
# - No Spam, no Virus
# - Spam, Virus
# - Spam, no Virus

import smtplib, os, getopt, sys
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders

# Initial setup, makes the rest shorter
rcpt = ''
inputfile = ''
virusfile = 'eicar.com'
server = ''
debug = 0

def print_usage():
	print "Usage: " + sys.argv[0] + "-r recipient -f virusfile -s server [ -i inputfile ] [-d debuglevel]"
	sys.exit(0)

try:
	opts, pargs = getopt.getopt(sys.argv[1:], 'r:f:s:d:i:')
except:
	print_usage()

for i in opts:
	if i[0] == '-r':
		rcpt = i[1]
	if i[0] == '-f':
		virusfile = i[1]
	if i[0] == '-s':
		server = i[1]
	if i[0] == '-d':
		debug = int(i[1])
	if i[0] == '-i':
		inputfile = i[1]

if not server:
	print "Please specify a server"
	print_usage()

if not rcpt and not inputfile:
	print "Specify recipient or use an inputfile"
	print_usage()

if debug < 0 or debug > 2:
	print "Debug must be one of 0, 1, 2, not %s" % debug
	print_usage()

def sendMail(to, subject, text, files=[],server="localhost"):
    assert type(to)==list
    assert type(files)==list
    fro = "Mail Test Skript <"+ os.environ['USER'] +"@univention.de>"

    msg = MIMEMultipart()
    msg['From'] = fro
    msg['To'] = COMMASPACE.join(to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach( MIMEText(text) )

    for file in files:
		part = MIMEBase('application', "octet-stream")
		part.set_payload( open(file,"rb").read() )
		Encoders.encode_base64(part)
		part.add_header('Content-Disposition', 'attachment; filename="%s"'
						% os.path.basename(file))
		msg.attach(part)

    smtp = smtplib.SMTP(server)
    if debug == 2:
	    smtp.set_debuglevel(1)
    smtp.sendmail(fro, to, msg.as_string() )
    smtp.close()

sendMail( [ rcpt ], "Mail ohne Spam mit Virus", "Der body", [ virusfile ], server)
sendMail( [ rcpt ], "Mail ohne Spam ohne Virus", "Der body", [], server)
sendMail( [ rcpt ], "Mail mit Spam mit Virus", "XJS*C4JDBQADN1.NSBN3*2IDNEN*GTUBE-STANDARD-ANTI-UBE-TEST-EMAIL*C.34X", [ virusfile ], server)
sendMail( [ rcpt ], "Mail mit Spam ohne Virus", "XJS*C4JDBQADN1.NSBN3*2IDNEN*GTUBE-STANDARD-ANTI-UBE-TEST-EMAIL*C.34X", [], server)
