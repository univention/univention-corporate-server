import univention.Apps
import univention.Constants

import univention.jobs.AppStatusViews
import univention.jobs.AppAutotestUpdateMultiEnv
import univention.jobs.AppAutotestMultiEnv
import univention.jobs.AppAutotestMultiEnvUpdateFrom
import univention.jobs.AppGenericTest

// Build parameters are exposed as environment variables in Jenkins.
// A seed job build parameter named FOO is available as FOO variable
// in the DSL scripts. See the section about environment variables above.

univention.Constants.VERSIONS.each {

    version = it.getKey()
    patch_level = it.getValue()['patch_level']
    last_version = it.getValue()['last_version']
    path = 'UCS-' + version + '/Apps'

    // create folder, generic app job and views
    folder(path)
    AppStatusViews.create(this, path)
    AppGenericTest.create(this, 'UCS-' + version, version, patch_level, last_version)

    // get apps for version and create folder and jobs
    apps = Apps.getApps(version, test=true, ucs_components=false)
    apps.keySet().sort().each { app ->
        app_path = path + '/' + app
        folder(app_path)
        AppAutotestUpdateMultiEnv.create(this, app_path, version, patch_level, apps[app])
        AppAutotestMultiEnv.create(this, app_path, version, patch_level, apps[app])
        AppAutotestMultiEnvUpdateFrom.create(this, app_path, version, patch_level, last_version, apps[app])
    }
}
