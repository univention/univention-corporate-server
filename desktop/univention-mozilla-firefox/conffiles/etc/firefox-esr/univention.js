@%@UCRWARNING=// @%@

@!@
for ffconf, ucrv in {
	'general.config.filename': 'firefox/prefs/conffile',
	'browser.shell.checkDefaultBrowser': 'firefox/prefs/checkdefaultbrowser',
	'spellchecker.dictionary': 'firefox/prefs/spellchecker/dictionary',
	'browser.startup.homepage': 'firefox/prefs/homepage',
	'browser.startup.homepage_reset': 'firefox/prefs/homepage',
	'startup.homepage_welcome_url': 'firefox/prefs/homepage',
	'print.print_command': 'firefox/prefs/print_command',
	'print.postscript.print_command': 'firefox/prefs/print_command',
}.iteritems():
	value = configRegistry.get(ucrv)
	if value:
		print 'pref("%s", "%s");' % (ffconf, value)
@!@
