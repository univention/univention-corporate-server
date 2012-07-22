#!/usr/bin/python2.4 
import foo
import bar

def main():
	print 'Boing'
	print _('Dieser Test ist ok')
	print _('Hier lieg auch %d Problem vor') % 0
	x = 'hier'
	raise "Error"

main()
