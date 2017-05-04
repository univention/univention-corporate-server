@!@
# vim: set ft=python:
from polib import POFile, POEntry
from datetime import datetime
import cgi
import ast
from univention.app_appliance import Apps
from univention.appcenter import get_action

appId = configRegistry.get('umc/web/appliance/id', '')
app = Apps().find(appId)
get = get_action('get')()
app_name = (app and app.name) or ''

po = POFile()
po.metadata = {
    'Project-Id-Version': 'univention-app-appliance',
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
po.append(POEntry(
	msgid='UCS Overview',
	msgstr='UCS Übersicht'
))
po.append(POEntry(
	msgid='Link to the UCS Overview',
	msgstr='Link zur UCS Übersicht'
))
po.append(POEntry(
	msgid='Link to the {name} webinterface'.format(name=cgi.escape(app_name)),
	msgstr='Link zur {name} Weboberfläche'.format(name=cgi.escape(app_name))
))

try:
	appliance_links_en = ast.literal_eval(list(get.get_values(app, [('Application', 'ApplianceLinks')]))[0][2])
	appliance_links_de = ast.literal_eval(list(get.get_values(app, [('de', 'ApplianceLinks')]))[0][2])
except (IndexError, AttributeError) as exception:
	pass
else:
	for appliance_link_en, appliance_link_de in zip(appliance_links_en, appliance_links_de):
			for attr in ['link', 'short', 'long']:
				po.append(POEntry(
					msgid=cgi.escape(appliance_link_en[attr]),
					msgstr=cgi.escape(appliance_link_de[attr])
				))

print po.to_binary()
@!@
