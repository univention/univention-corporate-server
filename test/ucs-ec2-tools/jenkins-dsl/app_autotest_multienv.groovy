import univention.Apps

// get location (and UCS version) from job name 
def loc = new File(JOB_NAME)
def workdir = loc.getParent()

// better get version from JOB_NAME
def version = '4.1'
def patch_level = '0'

// get apps from testing, without ucs components
apps = new Apps().getApps(version, test=true, ucs_components=false)

// just for testing, print found apps, but create jobs only for zarafa and dudle
apps.keySet().each { app ->
  println app
  println apps[app].get('roles')
}
def test_apps = [:]
test_apps['zarafa'] = [:]
test_apps['zarafa']['roles'] = ['master', 'backup', 'slave', 'memberserver']
test_apps['dudle'] = [:]
test_apps['dudle']['roles'] = ['master', 'backup']

// create matrix job for every app
test_apps.keySet()each { app ->
  
  // create folders
  folder(workdir + '/apps')
  folder(workdir + '/apps/' + app)
  
  // create job
  job_name = workdir + '/apps/' + app + '/App Autotest MultiEnv'
  matrixJob(job_name) {
    
    // config
    quietPeriod(60)
    logRotator(-1, 5, -1, -1)
    description("run job for ${app}")
    concurrentBuild()
    
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
      text('Systemrolle', test_apps[app].get('roles'))
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
sed -i "s|APP_ID|${app}|g" \$cfg
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
