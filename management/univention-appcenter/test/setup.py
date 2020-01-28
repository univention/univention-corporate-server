import json
import sqlite3

from univention.appcenter.app_cache import Apps
from univention.appcenter.app import App, AppBooleanAttribute, AppIntAttribute

conn = sqlite3.connect('apps.db')
c = conn.cursor()
#c.execute('CREATE TABLE apps (server TEXT NOT NULL, ucs_version TEXT NOT NULL, id TEXT NOT NULL, version TEXT NOT NULL, component_id TEXT NOT NULL, installed BOOLEAN, attrs TEXT NOT NULL)')
#for app in Apps().get_every_single_app():
#	c.execute('INSERT INTO apps VALUES (?, ?, ?, ?, ?, ?, ?)', (app.get_server(), app.get_ucs_version(), app.id, app.version, app.component_id, app.is_installed(), json.dumps(app.attrs_dict())))
#conn.commit()

attrs = []
for attr in sorted(App._attrs, cmp=lambda x, y: cmp(x.name, y.name)):
	key = 'app_attr_%s' % attr.name
	_type = 'TEXT'
	if isinstance(attr, AppBooleanAttribute):
		_type = 'INTEGER'
	if isinstance(attr, AppIntAttribute):
		_type = 'BOOLEAN'
	if hasattr(attr, 'required') and attr.required:
		_type = '%s NOT NULL' % _type
	attrs.append((key, _type))
stmt = 'CREATE TABLE apps (server TEXT NOT NULL, ucs_version TEXT NOT NULL, id TEXT NOT NULL, version TEXT NOT NULL, component_id TEXT NOT NULL, installed BOOLEAN, attrs TEXT NOT NULL, %s)' % (', '.join('%s %s' % (k, v) for k, v in attrs))
c.execute(stmt)

def make_value(v):
	if isinstance(v, (list, dict)):
		return str(v)
	return v

for app in Apps().get_every_single_app():
	values = [app.get_server(), app.get_ucs_version(), app.id, app.version, app.component_id, app.is_installed(), json.dumps(app.attrs_dict())]
	values.extend([make_value(getattr(app, k[9:])) for k, _ in attrs])
	c.execute('INSERT INTO apps VALUES (%s)' % ', '.join(['?'] * len(values)), tuple(values))
conn.commit()
