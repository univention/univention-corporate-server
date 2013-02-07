@!@
from polib import POFile, POEntry
from datetime import datetime
from univention.management.console.modules.appcenter.app_center import Application
from univention.lib.package_manager import PackageManager
from univention.management.console.resources import moduleManager
package_manager = PackageManager(lock=False)
moduleManager.load()
po = POFile()
po.metadata = {
    'Project-Id-Version': 'univention-management-console-module-apps',
    'Report-Msgid-Bugs-To': 'packages@univention.de',
    'POT-Creation-Date': 'Tue, 06 Feb 2013 18:47:26 +0200',
    'PO-Revision-Date': datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0200'),
    'Last-Translator': 'ucr commit <packages@univention.de>',
    'Language-Team': 'Univention GmbH <packages@univention.de>',
    'Language': 'de',
    'MIME-Version': '1.0',
    'Content-Type': 'text/plain; charset=UTF-8',
    'Content-Transfer-Encoding': '8bit',
}
entry = POEntry(
	msgid='Installed Applications',
	msgstr='Installierte Applikationen'
)
po.append(entry)
for app in Application.all(only_local=True, localize=False):
	if (app.get('umcmodule') or app.id) in moduleManager.modules():
		continue
	if not app.is_installed(package_manager):
		continue
	for attr in ('Name', 'Description'):
		try:
			msgid = msgstr=app.raw_config.get('Application', attr)
			msgstr = msgstr=app.raw_config.get('de', attr)
		except: # NoOptionError
			pass
		else:
			entry = POEntry(
				msgid=msgid,
				msgstr=msgstr
			)
			po.append(entry)
print po.to_binary()
@!@
