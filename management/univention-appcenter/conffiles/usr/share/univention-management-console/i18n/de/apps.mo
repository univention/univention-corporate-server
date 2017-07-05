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
	from univention.appcenter.app_cache import Apps
	apps = Apps().get_all_locally_installed_apps()
except ImportError:
	# this happens sometimes during release updates
	# ... an empty file is fine then
	apps = []
except:
	# well THIS is weird.
	# Anyway, just use an empty file. The problem will be visible as soon as the UMC module
	# is opened
	apps = []
for app in apps:
	for attr in ('name', 'description'):
		app_en = app.get_app_cache_obj().copy(locale='en').find_by_component_id(app.component_id)
		app_de = app.get_app_cache_obj().copy(locale='de').find_by_component_id(app.component_id)
		msgid = getattr(app_en, attr)
		msgstr = getattr(app_de, attr)
		if not msgid:
			continue
		entry = POEntry(
			msgid=msgid,
			msgstr=msgstr or ''
		)
		po.append(entry)
print po.to_binary()
@!@
