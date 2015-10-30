import univention.Apps
import univention.Constants

// Build parameters are exposed as environment variables in Jenkins.
// A seed job build parameter named FOO is available as FOO variable
// in the DSL scripts. See the section about environment variables above.

// get location (and UCS version) from job name 
def JOB_NAME = 'UCS-4.1/UCS-4.1-0/APP seed'
def loc = new File(JOB_NAME)
def workdir = loc.getParent()

def version = JOB_NAME.split('/')[0].replace('UCS-', '')
def patch_level = JOB_NAME.split('/')[1].replace('UCS-', '').replace(version, '').replace('-', '')

// better get version from JOB_NAME
println JOB_NAME

version = '4.1'
def last_version = univention.Constants.LAST_VERSION.get(version)
if (last_version == null) {
	throw new RuntimeException("last version for version ${version} not found")
}


// get apps from testing, without ucs components
apps = new Apps().getApps(version, test=true, ucs_components=false)

// create jobs for every app
apps.keySet()each { app ->
  
  //// create folders
  //println workdir + '/apps'
  //println workdir + '/apps/' + app
  //
  //// create matrix job App Autotest MultiEnv
  //path = workdir + '/apps/' + app

  //// create jobs
  //println "${app} ${path} ${version} ${patch_level}"

  //println apps[app].get('roles')
  //println apps[app].get('required_apps')
  createJob(apps[app])  

}

def createJob(Map app) {
    println " -> ${app.id}"

    if (app.required_apps) {
        println " ...${app.required_apps.join(' ')}..."
    }
}
