package univention

import java.util.zip.GZIPInputStream
import java.io.File
import groovy.json.JsonSlurper
import java.util.Properties
import univention.Constants

class Apps {

	static getApps(String version, Boolean test=true, Boolean ucs_components=false) {

		def server = 'appcenter.software-univention.de'
		if (test) {
			server = 'appcenter-test.software-univention.de'
		}
		def url = new URL("http://${server}/meta-inf/${version}/index.json.gz")
		def stream = new GZIPInputStream(url.newInputStream())
		def reader = new BufferedReader(new InputStreamReader(stream))
		def index = new JsonSlurper().parse(reader)

		def apps = [:]
        index.each {

            // get ini url
            def app = it.getValue()
            if (app.get('ini') == null || app.ini.get('url') == null) {
                return
            }
            app.ini.url = app.ini.url.replace('appcenter.test', 'appcenter-test')

            // get ini as property object
            url = new URL(app.ini.url)
            def properties = new java.util.Properties()
            properties.load(url.newInputStream())

            // ignore UCS components
            if (! ucs_components) {
                def categories = properties.getProperty('Categories')
                if (categories && categories.toLowerCase().contains('ucs components')) {
                    return
                }
            }

            // get ID
            def app_id = properties.getProperty('ID')
            if (app_id == null) {
                return
            }

            // get infos
            apps[app_id] = [:]
            apps[app_id]['id'] = app_id
            apps[app_id]['roles'] = []
            apps[app_id]['required_apps'] = []

            // requierd apps, always add app itself
            def required_apps = properties.getProperty('RequiredApps')
            if (required_apps) {
                required_apps.split(',').each {
                    apps[app_id]['required_apps'] << it
                }
            }
            apps[app_id]['required_apps'] << app_id

            // get roles
            def roles = properties.getProperty('ServerRole')
            if (roles == null) {
                roles = 'domaincontroller_master,domaincontroller_backup,domaincontroller_slave,memberserver'
            }
            roles.split(',').each { role ->
                if (univention.Constants.ROLE_MAPPING.get(role)) {
                    apps[app_id]['roles'] << univention.Constants.ROLE_MAPPING.get(role)
                }
            }
        }

		return apps
	}
}
