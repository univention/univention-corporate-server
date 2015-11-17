import univention.Apps
import univention.Constants
import univention.Jobs

// Build parameters are exposed as environment variables in Jenkins.
// A seed job build parameter named FOO is available as FOO variable
// in the DSL scripts. See the section about environment variables above.

// get location (and UCS version) from job name 
//def loc = new File(JOB_NAME)
//def workdir = loc.getParent()

univention.Constants.VERSIONS.each {

    version = it.getKey()
    patch_level = it.getValue()['patch_level']
    last_version = it.getValue()['last_version']
    path = 'UCS-' + version + '/Apps'

    // create folder, generic app jobs and views
    folder(path)
    Jobs.createAppStatusViews(this, path)

    // get apps for version and create folder and jobs
    apps = Apps.getApps(version, test=true, ucs_components=false)
    apps.keySet().sort().each { app ->
        app_path = path + '/' + app
        folder(app_path)
        Jobs.createAppAutotestUpdateMultiEnv(this, app_path, version, patch_level, apps[app])
        Jobs.createAppAutotestMultiEnv(this, app_path, version, patch_level, apps[app])
        Jobs.createAppAutotestMultiEnvUpdateFrom(this, app_path, version, patch_level, last_version, apps[app])
    }
}
