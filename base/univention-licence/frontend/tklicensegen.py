#!/usr/bin/python2.4
# -*- coding: utf-8 -*-

from Tkinter import *
import os
import string
import commands
import sre
import tkFileDialog
import time
from tkMessageBox import showinfo

class tkLicenseGen:
        def __init__(self,master):
                master.title('Univention Lizenz Generator')
                self.master=master
		self.logoframe=Frame(self.master,bg='red')
		self.logoframe.pack(side=TOP,fill=X,expand=YES)	
		self.lftopframes=LabelFrame(self.master)
		self.lftopframes.pack(side=TOP,fill=X,expand=YES)
		self.lframe=Frame(self.lftopframes)
		self.rframe=Frame(self.lftopframes)
		self.lframe.pack(side=LEFT,fill=X,expand=YES)
		self.rframe.pack(side=RIGHT,fill=X,expand=YES)
		
		self.bframe=Frame(self.master)
		self.bframe.pack(fill=X)

		self.kname=StringVar()
		self.kname.set('test')

		self.chkevar=IntVar()
		self.chkevar.set('1')
		self.chkivar=IntVar()
		self.chkovar=IntVar()
		self.chkdvar=IntVar()
		
		self.exday=StringVar()
		self.exmonth=StringVar()
		self.exyear=StringVar()
		self.getdate() #set date to localdate (month+3)

		self.logo=PhotoImage(file='/var/www/head_logo.gif')
		#self.logo.pack() #muss man nicht packen??!!
		self.logolabel=Label(self.logoframe,image=self.logo,bg='#CC3300')
		self.logolabel.pack(side=LEFT,fill=X,expand=YES)
		
		self.lfname=LabelFrame(self.lframe,font=("Helvetica", 11),text='Kundenname:')
		self.lfname.pack(fill=X)
		self.ekname=Entry(self.lfname,textvariable=self.kname,width=30)
		self.ekname.pack(side=LEFT)
	
		self.lfdate=LabelFrame(self.lframe,font=("Helvetica", 11),text='Ablaufdatum (TT/MM/JJ):')
		self.lfdate.pack(fill=X)
		self.eexd=Entry(self.lfdate,textvariable=self.exday,width=2)
		self.eexd.pack(side=LEFT)		
		self.eexm=Entry(self.lfdate,textvariable=self.exmonth,width=2)
		self.eexm.pack(side=LEFT)		
		self.eexy=Entry(self.lfdate,textvariable=self.exyear,width=2)
		self.eexy.pack(side=LEFT)	
		self.chkdate=Checkbutton(self.lfdate,text='Unbeschränkt',variable=self.chkdvar)
		self.chkdate.pack(side=RIGHT)
			

		self.lfchke=LabelFrame(self.lframe,font=("Helvetica", 11),text='Evaluationslizenz:')
		self.lfchke.pack(fill=X)
		self.chke=Checkbutton(self.lfchke, variable=self.chkevar)
		self.chke.pack(side=LEFT)

		self.lfchki=LabelFrame(self.lframe,font=("Helvetica", 11),text='Interne Lizenz:')
		self.lfchki.pack(fill=X)
		self.chki=Checkbutton(self.lfchki, variable=self.chkivar)
		self.chki.pack(side=LEFT)

		self.lfchko=LabelFrame(self.lframe,font=("Helvetica", 11),text='Altes Lizenzformat (vor 1.2-3):')
		self.lfchko.pack(fill=X)
		self.chko=Checkbutton(self.lfchko, variable=self.chkovar, command=self.makegrey)
		self.chko.pack(side=LEFT)

		
		self.kdn=StringVar()
		self.kdn.set('dc=univention,dc=de')
		self.lfdn=LabelFrame(self.rframe,font=("Helvetica", 11),text='Kunde DN:')
		self.lfdn.pack(fill=X)
		self.ekdn=Entry(self.lfdn,textvariable=self.kdn,width=30)
		self.ekdn.pack(side=LEFT)

		self.kmaxacc=IntVar()
		self.kmaxacc.set('999')
		self.kmaxgacc=IntVar()
		self.kmaxgacc.set('999')
		self.kmaxcli=IntVar()
		self.kmaxcli.set('999')
		self.kmaxdesk=IntVar()
		self.kmaxdesk.set('999')

		self.chkmaxaccvar=IntVar()
		self.chkmaxaccvar.set('0')
		self.chkmaxgaccvar=IntVar()
		self.chkmaxgaccvar.set('0')
		self.chkmaxclivar=IntVar()
		self.chkmaxclivar.set('0')
		self.chkmaxdeskvar=IntVar()
		self.chkmaxdeskvar.set('0')

		self.lfmaxacc=LabelFrame(self.rframe,font=("Helvetica", 11),text='Max. Accounts:')
		self.lfmaxacc.pack(fill=X)
		self.lfmaxgacc=LabelFrame(self.rframe,font=("Helvetica", 11),text='Max. Groupware Accounts:')
		self.lfmaxgacc.pack(fill=X)
		self.lfmaxcli=LabelFrame(self.rframe,font=("Helvetica", 11),text='Max. Clients:')
		self.lfmaxcli.pack(fill=X)
		self.lfmaxdesk=LabelFrame(self.rframe,font=("Helvetica", 11),text='Max. Univention Desktops:')
		self.lfmaxdesk.pack(fill=X)

		self.emaxacc=Entry(self.lfmaxacc,textvariable=self.kmaxacc)
		self.emaxacc.pack(side=LEFT)
		self.chkmaxacc=Checkbutton(self.lfmaxacc,text='Unbeschränkt',variable=self.chkmaxaccvar)
		self.chkmaxacc.pack(side=LEFT)

		self.emaxgacc=Entry(self.lfmaxgacc,textvariable=self.kmaxgacc)
		self.emaxgacc.pack(side=LEFT)
		self.chkmaxgacc=Checkbutton(self.lfmaxgacc,text='Unbeschränkt',variable=self.chkmaxgaccvar)
		self.chkmaxgacc.pack(side=LEFT)

		self.emaxcli=Entry(self.lfmaxcli,textvariable=self.kmaxcli)
		self.emaxcli.pack(side=LEFT)
		self.chkmaxcli=Checkbutton(self.lfmaxcli,text='Unbeschränkt',variable=self.chkmaxclivar)
		self.chkmaxcli.pack(side=LEFT)

		self.emaxdesk=Entry(self.lfmaxdesk,textvariable=self.kmaxdesk)
		self.emaxdesk.pack(side=LEFT)
		self.chkmaxdesk=Checkbutton(self.lfmaxdesk,text='Unbeschränkt',variable=self.chkmaxdeskvar)
		self.chkmaxdesk.pack(side=LEFT)

		self.bexit=Button(self.bframe,text='Beenden',command=self.quit)
		self.bexit.pack(side=RIGHT)

		self.bsave=Button(self.bframe,text='Lizenz erzeugen',command=self.generate)
		self.bsave.pack(side=RIGHT)

	def generate(self):
		makelicense='./make_license.sh '
		path=tkFileDialog.asksaveasfilename(initialdir='~',initialfile=self.kname.get()+'-license', defaultextension='.ldif')
		#print path
		if path:
			if self.chkevar.get():
				makelicense += '-e '
			if self.chkivar.get():
				makelicense += '-i '
			makelicense += '-f "%s" '%path
	
			if not self.chkdvar.get():
				makelicense += '-d "%s/%s/%s" '% (self.exmonth.get(), self.exday.get(), self.exyear.get())
	
			if not self.chkovar.get():
				if not self.chkmaxaccvar.get():
					makelicense += '-a %d '%self.kmaxacc.get()
				else:
					makelicense += '-a unlimited '
				if not self.chkmaxgaccvar.get():
					makelicense += '-g %d '%self.kmaxgacc.get()
				else:
					makelicense += '-g unlimited '
				if not self.chkmaxclivar.get():
					makelicense += '-c %d '%self.kmaxcli.get()
				else:
					makelicense += '-c unlimited '
				if not self.chkmaxdeskvar.get():
					makelicense += '-u %d '%self.kmaxdesk.get()
				else:
					makelicense += '-u unlimited '
			else:
				makelicense += '-o '
	
			makelicense += '"%s" '%self.kname.get()
			makelicense += '"%s"'%self.kdn.get()
			os.chdir('/home/groups/99_license/')
			i=commands.getstatusoutput(makelicense)
			if i[0]:
				if repr(i[0]) == '257':
					showinfo('Fehler','Errorcode: "%s"\nEvtl. sind Sie nicht in dem Sudoers File!'%repr(i[0]))
				elif repr(i[0]) == '8704':
					showinfo('Fehler','Errorcode: "%s"\nmake_license.sh meldet: "invalid DN"!'%repr(i[0]))
				else:
					showinfo('Fehler','Errorcode: "%s"\nEin unbekannter Fehler ist aufgetreten!\nBitte senden Sie eine komplette Fehlerbeschreibung an "support@univention.de"'%repr(i[0]))
			else:
				showinfo('Lizenz Erstellt!','Die Lizenz für %s wurde erfolgreich erstellt!'%self.kname.get())
			#print makelicense
			#print '-->ErrorCode: %d'%i[0]
			#print i[1]
		
	def getdate(self):	
		localtime=time.strftime('%d %m %y')
		split=string.split(localtime,' ')
		day=int(split[0])
		month=int(split[1])
		year=int(split[2])
		month+=3
		if month > 12:
			month = month - 12
			year+=1
		if day < 10:
			day = '0'+str(day)
		if month < 10:
			month = '0'+str(month)
		if year < 10:
			year = '0'+str(year)
		self.exday.set(day)
		self.exmonth.set(month)
		self.exyear.set(year)
	
	def makegrey(self):
		pass

        def quit(self,event=None):
                self.master.quit()

if __name__ == '__main__':
        root=Tk()
        licensegen=tkLicenseGen(root)
        root.mainloop()

