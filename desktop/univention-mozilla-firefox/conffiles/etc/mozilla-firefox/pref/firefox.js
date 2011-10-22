@%@UCRWARNING=// @%@

// This is the Debian specific preferences file for Mozilla Firefox
// You can make any change in here, it is the purpose of this file.
// You can, with this file and all files present in the
// /etc/mozilla-firefox/pref directory, override any preference that is
// present in /usr/lib/mozilla-firefox/defaults/pref directory.
// While your changes will be kept on upgrade if you modify files in
// /etc/mozilla-firefox/pref, please note that they won't be kept if you
// do them in /usr/lib/mozilla-firefox/defaults/pref.

pref("extensions.update.enabled", true);
pref("extensions.update.autoUpdateEnabled", false);
pref("extensions.update.autoUpdate", false);

// Use LANG environment variable to choose locale
pref("intl.locale.matchOS", true);

// Disable default browser checking.
pref("browser.shell.checkDefaultBrowser", false);

pref("print.print_command", "kprinter");
pref("print.postscript.print_command", "kprinter");
pref("print.postscript.paper_size", "A4");

@!@
if baseConfig.has_key('firefox/prefs/conffile') and baseConfig['firefox/prefs/conffile']:
	print 'pref("general.config.filename", "%s");' % baseConfig['firefox/prefs/conffile']
@!@

