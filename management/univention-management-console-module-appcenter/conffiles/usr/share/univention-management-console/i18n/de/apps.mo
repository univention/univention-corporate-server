@!@
from polib import POFile, POEntry
from datetime import datetime
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
try:
	from univention.management.console.modules.appcenter.app_center import Application
	from univention.lib.package_manager import PackageManager
	package_manager = PackageManager(lock=False)
except ImportError:
	# this happens sometimes during release updates
	# ... an empty file is fine then
	apps = []
except:
	# well THIS is weird. Probably PackageManager cannot open the cache (broken sources list?)
	# Anyway, just use an empty file. The problem will be visible as soon as the UMC module
	# is opened
	apps = []
else:
	apps = Application.all_installed(package_manager, only_local=True, localize=False)
for app in apps:
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
