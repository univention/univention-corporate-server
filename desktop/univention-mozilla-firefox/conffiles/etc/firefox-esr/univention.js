@%@UCRWARNING=// @%@

pref("general.config.obscure_value", 0);
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
	'network.negotiate-auth.trusted-uris': 'domainname',
}.iteritems():
	value = configRegistry.get(ucrv)
	if value:
		print 'pref("%s", "%s");' % (ffconf, value)
@!@
