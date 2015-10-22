// /var/lib/jenkins/workspace/Mitarbeiter/Felix Botner/App Autotest MultiEnv Seed/univention
// but should be checked out from svn
import univention.Apps

apps = new Apps().getApps('4.1', test=true)

apps.keySet().each { app ->
  println app
  println apps[app].get('roles')
}

// just for testing
def test_apps = [:]
test_apps['zarafa'] = [:]
test_apps['zarafa']['roles'] = ['master', 'backup', 'slave', 'memberserver']
test_apps['dudle'] = [:]
test_apps['dudle']['roles'] = ['master', 'backup']

// get location (and UCS version) from job name 
def loc = new File(JOB_NAME)
workdir = loc.getParent()
name = loc.getName()

//hudson.FilePath workspace = hudson.model.Executor.currentExecutor().getCurrentWorkspace()
//println workspace


// create matrix job for every app (only)
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
        location('svn+ssh://svnsync@billy/var/svn/dev/branches/ucs-4.1/ucs-4.1-0/test/ucs-ec2-tools') {    
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
