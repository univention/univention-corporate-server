#!/usr/bin/python

import sys
import os
import re
import time

def buildPDF( file ):
	res = os.system('TEXINPUTS=.:..:../..:../../..:../../../..:../../../../..: pdflatex -halt-on-error -interaction=nonstopmode -file-line-error "%s"' % (file,))
	if res != 0:
		return res

	base = file[:-len('.tex')]
	if os.path.exists('%s.ndx' % (base,)):
		os.system('TEXINPUTS=.:..:../..:../../..:../../../..:../../../../..: makeindex -o "%s.nnd" "%s.ndx"' % (base, base))

	os.system('TEXINPUTS=.:..:../..:../../..:../../../..:../../../../..: bibtex "%s"' % (base,))
	res = os.system('TEXINPUTS=.:..:../..:../../..:../../../..:../../../../..: pdflatex -halt-on-error -interaction=nonstopmode -file-line-error "%s"' % (file,))
	if res != 0:
		return res

	if os.path.exists('%s.ndx' % (base,)):
		os.system('TEXINPUTS=.:..:../..:../../..:../../../..:../../../../..: makeindex -o "%s.nnx" "%s.ndx"' % (base, base))

	res = os.system('TEXINPUTS=.:..:../..:../../..:../../../..:../../../../..: pdflatex -halt-on-error -interaction=nonstopmode -file-line-error "%s"' % (file,))

	return res

def printLogLines( msg, list ):
	print '------------------------------'
	print msg.center(30)
	print '------------------------------'
	for i in list:
		print '  ', i.replace('\n','')
	print ''


def checkLog( file ):
	fh = open( file )
	content = fh.read()
	fh.close()
	re_warn_undefref = re.compile('(^LaTeX Warning: Reference .*? on.*?[0-9]+.?$)', re.DOTALL | re.MULTILINE | re.IGNORECASE)
	re_warn_all = re.compile('(^LaTeX Warning: (?!Reference).*?$)', re.DOTALL | re.MULTILINE | re.IGNORECASE)
	re_error_all = re.compile('(^LaTeX Error:.*?$)', re.DOTALL | re.MULTILINE | re.IGNORECASE)
	re_build_again = re.compile('(^LaTeX Warning: Label.*? may have changed. Rerun to get cross-references right.)', re.DOTALL | re.MULTILINE | re.IGNORECASE)

	cnt_warn = 0
	cnt_error = 0
	do_rebuild = 0

	print '\n\n'
	res = re_warn_undefref.findall(content)
	if res:
		printLogLines('undefined references', res)

	res = re_warn_all.findall(content)
	if res:
		printLogLines('warnings', res)
		cnt_warn = len(res)

	res = re_error_all.findall(content)
	if res:
		printLogLines('errors', res)
		cnt_error = len(res)

	res = re_build_again.findall(content)
	if res:
		do_rebuild = 1
		print '---------------------------------------------------------------------'
		print '  SOME LABELS MAY HAVE CHANGED! RERUN TO GET CROSS-REFERENCE RIGHT!'
		print '---------------------------------------------------------------------'

	return (cnt_warn, cnt_error, do_rebuild)



def changeRevisionInFile( file, revision ):
	os.system('sed -i "s|ucsSVNVersion}{.*}|ucsSVNVersion}{%d}|" %s' % (revision, file))

def getSVNRevisionFromFile( file ):
	result = os.popen('LC_ALL=C svn info %s' % file )
	revision = '0'

	for line in result.readlines():
		if line.startswith('Last Changed Rev:'):
			revision = line.replace('Last Changed Rev: ', '').strip(' \r\n')
	return int(revision)

def getRevisionFromFile( file ):
	result = os.popen("grep ucsSVNVersion %s |sed -e 's|.*ucsSVNVersion}{||' | sed -e 's|}||'" % file )
	lines = result.readlines()
	if len(lines) > 0:
		return int(lines[-1].strip(' \r\n'))
	else:
		return 0

def getIncludes( file, filelist ):
	temp_files = []

	fp = open( file )
	for line in fp.readlines():
		if line.startswith('\input{'):
			name = line.replace('\input{', '').replace('}','.tex').strip(' \r\n')
			if name.endswith('.tex.tex'):
				name = name.replace('.tex.tex', '.tex')

			if not os.path.exists(name):
				path = name
				for i in range(1,20):
					path = os.path.join('..', path)
					if os.path.exists(path):
						name = path
						break

			if not name in filelist:
				filelist.append(name)
				temp_files.append(name)

	fp.close()

	for f in temp_files:
		filelist=getIncludes(f, filelist)

	return filelist


def main( ):
	for file in sys.argv[1:]:

		dir = os.path.dirname(file)
		if dir:
			os.chdir(dir)
		file = os.path.basename(file)

		svnRevision = getSVNRevisionFromFile( file )
		fileRevision = getRevisionFromFile( file )

		filelist = getIncludes( file, [] )

		for f in filelist:
			tmp_revision = getSVNRevisionFromFile( f )
			if tmp_revision > svnRevision:
				svnRevision = tmp_revision


		if svnRevision != fileRevision:
			changeRevisionInFile( file, svnRevision )
			print "####### change revision from %s to %s" % ( fileRevision, svnRevision)

		max_builds = 5

		while max_builds > 0:
			res = buildPDF( file )
			max_builds -= 1

			if res != 0:
				print ''
				print 'pdf-latex.py: exitcode is %s - stopping here' % res
				break
			else:
				result = checkLog( file.replace(".tex", ".log") )
				if result[2] == 1:
					time.sleep(2)
				else:
					break

		if res != 0:
			sys.exit( 1 )


if __name__ == "__main__":
	main()
