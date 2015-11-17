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
createStatusViews(workdir + '/Apps')

// create jobs for every app
apps.keySet().sort().each { app ->
  
  // create app folder
  folder(workdir + '/Apps/' + app)
  
  // create matrix job App Autotest MultiEnv
  path = workdir + '/Apps/' + app

  println path
  new Jobs().createAppAutotestUpdateMultiEnv(path, version, patch_level, apps[app])
  // create jobs
  //createAppAutotestMultiEnv(path, version, patch_level, apps[app])
  //createAppAutotestUpdateMultiEnv(path, version, patch_level, apps[app])
  //createAppAutotestMultiEnvUpdateFrom(path, version, patch_level, last_version, apps[app])
  //...

}

def createStatusViews(String path) {

    // stable
    listView(path + '/Stable') {
        description('Show all successful app test')
        recurse()
        jobFilters {
            status {
                matchType(MatchType.INCLUDE_MATCHED)
                status(Status.STABLE)
            }
        }
        columns {
            status()
            weather()
            name()
            lastSuccess()
            lastFailure()
            lastDuration()
            buildButton()
        }
    }

    // failed
    listView(path + '/Failed') {
        description('Show all failed app test')
        recurse()
        jobFilters {
            status {
                matchType(MatchType.INCLUDE_MATCHED)
                status(Status.UNSTABLE)
                status(Status.FAILED)
                status(Status.ABORTED)
            }
        }
        columns {
            status()
            weather()
            name()
            lastSuccess()
            lastFailure()
            lastDuration()
            buildButton()
        }
    }

    // running
    listView(path + '/Running') {
        description('Show all running app test')
        recurse()
    configure { view ->
        view / 'jobFilters' / 'hudson.views.BuildStatusFilter' {
            includeExcludeTypeString 'includeMatched'
            neverBuilt false
            building true
            inBuildQueue true
        }
    }
        columns {
            status()
            weather()
            name()
            lastSuccess()
            lastFailure()
            lastDuration()
            buildButton()
        }
    }

}

def createAppAutotestMultiEnvUpdateFrom(String path, String version, String patch_level, String last_version, Map app) {

  def desc = "App Autotest MultiEnv Release Update"
  def job_name = path + '/' + desc

  matrixJob(job_name) {

    authenticationToken('secret')

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
      archiveArtifacts('**/autotest-*.log,**/ucs-test.log,**/updater.log,**/setup.log,**/join.log,**/*.log')
      archiveJunit('**/test-reports/**/*.xml')
    }
  }
}

def createAppAutotestMultiEnv(String path, String version, String patch_level, Map app) {

  def desc = 'App Autotest MultiEnv'
  def job_name = path + '/' + desc

  matrixJob(job_name) {

    authenticationToken('secret')
    
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
      archiveArtifacts('**/autotest-*.log,**/ucs-test.log,**/updater.log,**/setup.log,**/join.log,**/*.log')
      archiveJunit('**/test-reports/**/*.xml')
    }
  }

}

def createAppAutotestUpdateMultiEnv(String path, String version, String patch_level, Map app) {

  def desc = 'App Autotest Update MultiEnv'
  def job_name = path + '/' + desc

  matrixJob(job_name) {

    authenticationToken('secret')
    
    // config
    quietPeriod(60)
    logRotator(-1, 5, -1, -1)
    description("run ${desc} for ${app.id}")
    concurrentBuild()

    // build parameters
    parameters {
      booleanParam('HALT', true, 'uncheck to disable shutdown of ec2 instances')
      booleanParam('Update_to_testing_errata_updates', false, 'Update to unreleased errata updates from updates-test.software-univention.de?')
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
cfg="examples/jenkins/autotest-12*-appupdate-\${Systemrolle}-\${SambaVersion}.cfg"
sed -i "s|APP_ID|${app.required_apps.join(' ')}|g" \$cfg
test "\$Update_to_testing_errata_updates" = true && sed -i "s|upgrade_to_latest_errata|upgrade_to_latest_test_errata|g" \$cfg
exec ./ucs-ec2-create -c \$cfg"""
      shell(cmd)
    }
    
    // post build
    publishers {
      archiveArtifacts('**/autotest-*.log,**/ucs-test.log,**/updater.log,**/setup.log,**/join.log,**/*.log')
      archiveJunit('**/test-reports/**/*.xml')
    }
  }

}
