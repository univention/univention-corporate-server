package univention

import java.util.zip.GZIPInputStream
import java.io.File
import groovy.json.JsonSlurper
import java.util.Properties
import univention.Constants

class Apps {

	def getApps(String version, Boolean test=true, Boolean ucs_components=false) {

		def server = 'appcenter.software-univention.de'
		if (test) {
			server = 'appcenter-test.software-univention.de'
		}
		def url = new URL("http://${server}/meta-inf/${version}/index.json.gz")
		def stream = new GZIPInputStream(url.newInputStream())
		def reader = new BufferedReader(new InputStreamReader(stream))
		def index = new JsonSlurper().parse(reader)

		def apps = [:]
		index.keySet().sort().each {
			def app = it.split('_')
			if (app.size() == 1) {
				version = '00000000'
			} else {
				version = app[1]
			}
			if (index."$it".get('ini') == null) {
				return 
			}
			if (index."$it".ini.get('url') == null) {
				return
			}
			def name = app[0]
			if (apps.get(name) == null) {
				apps[name] = [:]
				apps[name]['version'] = version
				apps[name]['ini'] = index."$it".ini.url.replace('appcenter.test', 'appcenter-test')
			} else {
		    	if (version > apps[name]['version']) {
		        	apps[name]['version'] = version
		        	apps[name]['ini'] = index."$it".ini.url.replace('appcenter.test', 'appcenter-test')
		    	}
			}
		}

		def ret_val = [:]
		apps.keySet().sort().each { name ->


			// get ini as property object
			url = new URL(apps."$name".ini)
			def properties = new java.util.Properties()
			properties.load(url.newInputStream())

			// ignore UCS components
			if (! ucs_components) {
				def categories = properties.getProperty('Categories')
				if (categories && categories.toLowerCase().contains('ucs components')) {
					return
				}
			}

			def app_id = properties.getProperty('ID')
			if (app_id == null) {
				return
			}

			ret_val[app_id] = [:]
			ret_val[app_id]['id'] = app_id
			ret_val[app_id]['roles'] = []
			ret_val[app_id]['required_apps'] = []

			// requierd apps, always add app itself
			def required_apps = properties.getProperty('RequiredApps')
			if (required_apps) {
				required_apps.split(',').each {
					ret_val[app_id]['required_apps'] << it
				}
			}
			ret_val[app_id]['required_apps'] << app_id

			// get roles
			def roles = properties.getProperty('ServerRole')
			if (roles == null) {
				roles = 'domaincontroller_master,domaincontroller_backup,domaincontroller_slave,memberserver'
			}
			roles.split(',').each { role ->
				if (univention.Constants.ROLE_MAPPING.get(role)) {
					ret_val[app_id]['roles'] << univention.Constants.ROLE_MAPPING.get(role)
				}
			}
		}

		return ret_val
	}
}
