import univention.Apps
import univention.Constants
import univention.Jobs

// Build parameters are exposed as environment variables in Jenkins.
// A seed job build parameter named FOO is available as FOO variable
// in the DSL scripts. See the section about environment variables above.

// get location (and UCS version) from job name 
def loc = new File(JOB_NAME)
def workdir = loc.getParent()

// better get version from JOB_NAME
println JOB_NAME
println workdir
def version = '4.1'
def patch_level = '0'
def last_version = univention.Constants.LAST_VERSION.get(version)

if (last_version == null) {
	throw new RuntimeException("last version for version ${version} not found")
}

// get apps from testing, without ucs components
apps = new Apps().getApps(version, test=true, ucs_components=false)

// create folder and views
folder(workdir + '/Apps')
//createStatusViews(workdir + '/Apps')
Jobs.createAppStatusViews(this, workdir + '/Apps')

// create jobs for every app
apps.keySet().sort().each { app ->
  
  // create app folder
  folder(workdir + '/Apps/' + app)
  
  // create matrix job App Autotest MultiEnv
  path = workdir + '/Apps/' + app

  Jobs.createAppAutotestUpdateMultiEnv(this, path, version, patch_level, apps[app])
  Jobs.createAppAutotestMultiEnv(path, version, patch_level, apps[app])
  Jobs.createAppAutotestMultiEnvUpdateFrom(path, version, patch_level, last_version, apps[app])
  //...

}
