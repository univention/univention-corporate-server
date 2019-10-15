#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Univention License
#  Tk-Frontend for univention_make_license
#
# Copyright 2004-2019 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.

from Tkinter import Frame, TOP, X, YES, LabelFrame, LEFT, RIGHT, StringVar, IntVar, PhotoImage, Label, Entry, Checkbutton, TclError, Button, Tk
import os
import sys
import subprocess
import tkFileDialog
import time
from tkMessageBox import showinfo, showerror


class tkLicenseGen:

	def __init__(self, master):
		master.title('Univention Lizenz Generator')
		self.master = master
		self.logoframe = Frame(self.master, bg='red')
		self.logoframe.pack(side=TOP, fill=X, expand=YES)
		self.lftopframes = LabelFrame(self.master)
		self.lftopframes.pack(side=TOP, fill=X, expand=YES)
		self.lframe = Frame(self.lftopframes)
		self.rframe = Frame(self.lftopframes)
		self.lframe.pack(side=LEFT, fill=X, expand=YES)
		self.rframe.pack(side=RIGHT, fill=X, expand=YES)

		self.bframe = Frame(self.master)
		self.bframe.pack(fill=X)

		self.kname = StringVar()
		self.kname.set('test')

		self.chkevar = IntVar()
		self.chkevar.set('1')
		self.chkivar = IntVar()
		self.chkovar = IntVar()
		self.chkdvar = IntVar()

		self.exday = StringVar()
		self.exmonth = StringVar()
		self.exyear = StringVar()
		self.getdate()  # set date to localdate (month+3)

		try:
			self.logo = PhotoImage(file='/var/www/head_logo.gif')
		except TclError:  # fall back to 64x64 white
			self.logo = PhotoImage(data='R0lGODdhQABAAIAAAP///wAAACwAAAAAQABAAAACRYSPqcvtD6OctNqLs968+w+G4kiW5omm6sq27gvH8kzX9o3n+s73/g8MCofEovGITCqXzKbzCY1Kp9Sq9YrNarfcrhdQAAA7')
		# self.logo.pack() #muss man nicht packen??!!
		self.logolabel = Label(self.logoframe, image=self.logo, bg='#CC3300')
		self.logolabel.pack(side=LEFT, fill=X, expand=YES)

		self.lfname = LabelFrame(self.lframe, font=("Helvetica", 11), text='Kundenname:')
		self.lfname.pack(fill=X)
		self.ekname = Entry(self.lfname, textvariable=self.kname, width=30)
		self.ekname.pack(side=LEFT)

		self.lfdate = LabelFrame(self.lframe, font=("Helvetica", 11), text='Ablaufdatum (TT/MM/JJ):')
		self.lfdate.pack(fill=X)
		self.eexd = Entry(self.lfdate, textvariable=self.exday, width=2)
		self.eexd.pack(side=LEFT)
		self.eexm = Entry(self.lfdate, textvariable=self.exmonth, width=2)
		self.eexm.pack(side=LEFT)
		self.eexy = Entry(self.lfdate, textvariable=self.exyear, width=2)
		self.eexy.pack(side=LEFT)
		self.chkdate = Checkbutton(self.lfdate, text='Unbeschränkt', variable=self.chkdvar)
		self.chkdate.pack(side=RIGHT)

		self.lfchke = LabelFrame(self.lframe, font=("Helvetica", 11), text='Evaluationslizenz:')
		self.lfchke.pack(fill=X)
		self.chke = Checkbutton(self.lfchke, variable=self.chkevar)
		self.chke.pack(side=LEFT)

		self.lfchki = LabelFrame(self.lframe, font=("Helvetica", 11), text='Interne Lizenz:')
		self.lfchki.pack(fill=X)
		self.chki = Checkbutton(self.lfchki, variable=self.chkivar)
		self.chki.pack(side=LEFT)

		self.lfchko = LabelFrame(self.lframe, font=("Helvetica", 11), text='Altes Lizenzformat (vor 1.2-3):')
		self.lfchko.pack(fill=X)
		self.chko = Checkbutton(self.lfchko, variable=self.chkovar, command=self.makegrey)
		self.chko.pack(side=LEFT)

		self.kdn = StringVar()
		self.kdn.set('dc=univention,dc=de')
		self.lfdn = LabelFrame(self.rframe, font=("Helvetica", 11), text='Kunde DN:')
		self.lfdn.pack(fill=X)
		self.ekdn = Entry(self.lfdn, textvariable=self.kdn, width=30)
		self.ekdn.pack(side=LEFT)

		self.kmaxacc = IntVar()
		self.kmaxacc.set('999')
		self.kmaxgacc = IntVar()
		self.kmaxgacc.set('999')
		self.kmaxcli = IntVar()
		self.kmaxcli.set('999')
		self.kmaxdesk = IntVar()
		self.kmaxdesk.set('999')

		self.chkmaxaccvar = IntVar()
		self.chkmaxaccvar.set('0')
		self.chkmaxgaccvar = IntVar()
		self.chkmaxgaccvar.set('0')
		self.chkmaxclivar = IntVar()
		self.chkmaxclivar.set('0')
		self.chkmaxdeskvar = IntVar()
		self.chkmaxdeskvar.set('0')

		self.lfmaxacc = LabelFrame(self.rframe, font=("Helvetica", 11), text='Max. Accounts:')
		self.lfmaxacc.pack(fill=X)
		self.lfmaxgacc = LabelFrame(self.rframe, font=("Helvetica", 11), text='Max. Groupware Accounts:')
		self.lfmaxgacc.pack(fill=X)
		self.lfmaxcli = LabelFrame(self.rframe, font=("Helvetica", 11), text='Max. Clients:')
		self.lfmaxcli.pack(fill=X)
		self.lfmaxdesk = LabelFrame(self.rframe, font=("Helvetica", 11), text='Max. Univention Desktops:')
		self.lfmaxdesk.pack(fill=X)

		self.emaxacc = Entry(self.lfmaxacc, textvariable=self.kmaxacc)
		self.emaxacc.pack(side=LEFT)
		self.chkmaxacc = Checkbutton(self.lfmaxacc, text='Unbeschränkt', variable=self.chkmaxaccvar)
		self.chkmaxacc.pack(side=LEFT)

		self.emaxgacc = Entry(self.lfmaxgacc, textvariable=self.kmaxgacc)
		self.emaxgacc.pack(side=LEFT)
		self.chkmaxgacc = Checkbutton(self.lfmaxgacc, text='Unbeschränkt', variable=self.chkmaxgaccvar)
		self.chkmaxgacc.pack(side=LEFT)

		self.emaxcli = Entry(self.lfmaxcli, textvariable=self.kmaxcli)
		self.emaxcli.pack(side=LEFT)
		self.chkmaxcli = Checkbutton(self.lfmaxcli, text='Unbeschränkt', variable=self.chkmaxclivar)
		self.chkmaxcli.pack(side=LEFT)

		self.emaxdesk = Entry(self.lfmaxdesk, textvariable=self.kmaxdesk)
		self.emaxdesk.pack(side=LEFT)
		self.chkmaxdesk = Checkbutton(self.lfmaxdesk, text='Unbeschränkt', variable=self.chkmaxdeskvar)
		self.chkmaxdesk.pack(side=LEFT)

		self.bexit = Button(self.bframe, text='Beenden', command=self.quit)
		self.bexit.pack(side=RIGHT)

		self.bsave = Button(self.bframe, text='Lizenz erzeugen', command=self.generate)
		self.bsave.pack(side=RIGHT)

	def generate(self):
		makelicense = ['univention_make_license']
		path = tkFileDialog.asksaveasfilename(initialdir='~', initialfile=self.kname.get() + '-license', defaultextension='.ldif')
		# print path
		if path:
			if self.chkevar.get():
				makelicense.append('-e')
			if self.chkivar.get():
				makelicense.append('-i')
			makelicense.append('-f')
			makelicense.append(path)

			if not self.chkdvar.get():
				makelicense.append('-d')
				makelicense.append("%s/%s/%s" % (self.exmonth.get(), self.exday.get(), self.exyear.get()))

			if not self.chkovar.get():
				if not self.chkmaxaccvar.get():
					makelicense.append('-a')
					makelicense.append('%d' % self.kmaxacc.get())
				else:
					makelicense.append('-a')
					makelicense.append('unlimited')
				if not self.chkmaxgaccvar.get():
					makelicense.append('-g')
					makelicense.append('%d' % self.kmaxgacc.get())
				else:
					makelicense.append('-g')
					makelicense.append('unlimited')
				if not self.chkmaxclivar.get():
					makelicense.append('-c')
					makelicense.append('%d' % self.kmaxcli.get())
				else:
					makelicense.append('-c')
					makelicense.append('unlimited')
				if not self.chkmaxdeskvar.get():
					makelicense.append('-u')
					makelicense.append('%d' % self.kmaxdesk.get())
				else:
					makelicense.append('-u')
					makelicense.append('unlimited')
			else:
				makelicense.append('-o')

			makelicense.append(self.kname.get())
			makelicense.append(self.kdn.get())
			os.chdir('/home/groups/99_license/')
			p = subprocess.Popen(makelicense, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
			stdout, stderr = p.communicate()
			if p.returncode == 0:
				showinfo('Lizenz Erstellt!', 'Die Lizenz für %s wurde erfolgreich erstellt!' % self.kname.get())
			elif p.returncode == 257:
				showerror('Fehler', 'Errorcode: "%s"\nEvtl. sind Sie nicht in dem Sudoers File!' % p.returncode)
			elif p.returncode == 8704:
				showerror('Fehler', 'Errorcode: "%s"\nmake_license.sh meldet: "invalid DN"!' % p.returncode)
			else:
				print >>sys.stderr, '%r\n%s' % (makelicense, stdout)
				showerror('Fehler', 'Errorcode: "%s"\nEin unbekannter Fehler ist aufgetreten!\nBitte senden Sie eine komplette Fehlerbeschreibung an "support@univention.de"' % p.returncode)
			# print makelicense
			# print '-->ErrorCode: %d'%i[0]
			# print i[1]

	def getdate(self):
		localtime = time.strftime('%d %m %y')
		split = localtime.split(' ')
		day = int(split[0])
		month = int(split[1])
		year = int(split[2])
		month += 3
		if month > 12:
			month = month - 12
			year += 1
		if day < 10:
			day = '0' + str(day)
		if month < 10:
			month = '0' + str(month)
		if year < 10:
			year = '0' + str(year)
		self.exday.set(day)
		self.exmonth.set(month)
		self.exyear.set(year)

	def makegrey(self):
		pass

	def quit(self, event=None):
		self.master.quit()


if __name__ == '__main__':
	root = Tk()
	licensegen = tkLicenseGen(root)
	root.mainloop()
