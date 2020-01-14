import json
import sqlite3

from univention.appcenter.app_cache import Apps

conn = sqlite3.connect('apps.db')
c = conn.cursor()
c.execute('CREATE TABLE apps (server TEXT NOT NULL, ucs_version TEXT NOT NULL, id TEXT NOT NULL, version TEXT NOT NULL, component_id TEXT NOT NULL, attrs TEXT NOT NULL)')
for app in Apps().get_every_single_app():
	c.execute('INSERT INTO apps VALUES (?, ?, ?, ?, ?, ?)', (app.get_server(), app.get_ucs_version(), app.id, app.version, app.component_id, json.dumps(app.attrs_dict())))
conn.commit()

