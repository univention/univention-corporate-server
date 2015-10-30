import univention.Apps
import univention.Constants

// Build parameters are exposed as environment variables in Jenkins.
// A seed job build parameter named FOO is available as FOO variable
// in the DSL scripts. See the section about environment variables above.

// get location (and UCS version) from job name 
def loc = new File(JOB_NAME)
def workdir = loc.getParent()

// better get version from JOB_NAME
println JOB_NAME
def version = '4.1'
def patch_level = '0'
def last_version = univention.Constants.LAST_VERSION.get(version)

if (last_version == null) {
	throw new RuntimeException("last version for version ${version} not found")
}

// get apps from testing, without ucs components
apps = new Apps().getApps(version, test=true, ucs_components=false)

// create jobs for every app
apps.keySet()each { app ->
  
  // create folders
  folder(workdir + '/apps')
  folder(workdir + '/apps/' + app)
  
  // create matrix job App Autotest MultiEnv
  path = workdir + '/apps/' + app

  // create jobs
  createAppAutotestMultiEnv(path, version, patch_level, apps[app])
  createAppAutotestMultiEnvUpdateFrom(path, version, patch_level, last_version, apps[app])
  //...

}

def createAppAutotestMultiEnvUpdateFrom(String path, String version, String patch_level, String last_version, Map app) {

  def desc = "App Autotest MultiEnv Release Update"
  def job_name = path + '/' + desc

  matrixJob(job_name) {

    // config
    quietPeriod(60)
    logRotator(-1, 5, -1, -1)
    description("run ${desc} for ${app.id} (update from ${last_version} to ${version})")
    concurrentBuild()

    // build parameters
    parameters {
      booleanParam('HALT', true, 'uncheck to disable shutdown of ec2 instances')
    }

    // svn
    scm {
      svn {
        checkoutStrategy(SvnCheckoutStrategy.CHECKOUT)
        location("svn+ssh://svnsync@billy/var/svn/dev/branches/ucs-${version}/ucs-${version}-${patch_level}/test/ucs-ec2-tools") {
          credentials('50021505-442b-438a-8ceb-55ea76d905d3')
        }
        configure { scmNode ->
          scmNode / browser(class: 'hudson.plugins.websvn2.WebSVN2RepositoryBrowser') {
            url('https://billy.knut.univention.de/websvn/listing.php/?repname=dev')
            baseUrl('https://billy.knut.univention.de/websvn/')
            repname('repname=dev')
          }
        }
      }
    }

    // axies
    axes {
      text('Systemrolle', app.roles)
      text('SambaVersion', 's3', 's4')
    }

    // wrappers
    wrappers {
      preBuildCleanup()
    }

    // build step
    steps {
      cmd = """
cfg="examples/jenkins/autotest-11*-update-${last_version}-to-${version}-appupdate-\${Systemrolle}-\${SambaVersion}.cfg"
sed -i "s|APP_ID|${app.required_apps.join(' ')}|g" \$cfg
sed -i "s|%PARAM_HALT%|\$HALT|g" \$cfg
exec ./ucs-ec2-create -c \$cfg"""
      shell(cmd)
    }

    // post build
    publishers {
      archiveArtifacts('**/autotest-*.log,**/ucs-test.log')
      archiveJunit('**/test-reports/**/*.xml')
    }
  }
}

def createAppAutotestMultiEnv(String path, String version, String patch_level, Map app) {

  def desc = 'App Autotest MultiEnv'
  def job_name = path + '/' + desc

  matrixJob(job_name) {
    
    // config
    quietPeriod(60)
    logRotator(-1, 5, -1, -1)
    description("run ${desc} for ${app.id}")
    concurrentBuild()

    // build parameters
    parameters {
      booleanParam('HALT', true, 'uncheck to disable shutdown of ec2 instances')
    }
    
    // svn
    scm {
      svn {
        checkoutStrategy(SvnCheckoutStrategy.CHECKOUT)
        location("svn+ssh://svnsync@billy/var/svn/dev/branches/ucs-${version}/ucs-${version}-${patch_level}/test/ucs-ec2-tools") {
          credentials('50021505-442b-438a-8ceb-55ea76d905d3')    
        }
        configure { scmNode ->
          scmNode / browser(class: 'hudson.plugins.websvn2.WebSVN2RepositoryBrowser') {
            url('https://billy.knut.univention.de/websvn/listing.php/?repname=dev')
            baseUrl('https://billy.knut.univention.de/websvn/')
            repname('repname=dev')      
          }
        }
      }
    }
    
    // axies
    axes {
      text('Systemrolle', app.roles)
      text('SambaVersion', 's3', 's4')
    }
    
    // wrappers
    wrappers {
      preBuildCleanup()
    }
    
    // build step
    steps {
      cmd = """
cfg="examples/jenkins/autotest-10*-app-\${Systemrolle}-\${SambaVersion}.cfg"
sed -i "s|APP_ID|${app.required_apps.join(' ')}|g" \$cfg
sed -i "s|%PARAM_HALT%|\$HALT|g" \$cfg
exec ./ucs-ec2-create -c \$cfg"""
      shell(cmd)
    }
    
    // post build
    publishers {
      archiveArtifacts('**/autotest-*.log,**/ucs-test.log')
      archiveJunit('**/test-reports/**/*.xml')
    }
  }

}
