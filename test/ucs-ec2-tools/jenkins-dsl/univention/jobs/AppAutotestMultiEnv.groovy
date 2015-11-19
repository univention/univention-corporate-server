package univention.jobs

class AppAutotestMultiEnv {
  static create(dslFactory, String path, String version, String patch_level, Map app) {
    dslFactory.matrixJob(path + '/App Autotest MultiEnv') {
      // config
      authenticationToken('secret')
      quietPeriod(60)
      logRotator(-1, 5, -1, -1)
      description("1. Switch to Test App Center and install the given apps<br/>2. Run ucs-test<br/>3. Uninstall the given apps<br/>4. Run appcenter uninstall test")
      concurrentBuild()
      // build parameters
      parameters {
        booleanParam('HALT', true, 'uncheck to disable shutdown of ec2 instances')
        stringParam('patch_level', "${patch_level}", "test this patch level version of UCS ${version}")
      }
      // svn
      scm {
        svn {
          checkoutStrategy(SvnCheckoutStrategy.CHECKOUT)
          location("svn+ssh://svnsync@billy/var/svn/dev/branches/ucs-${version}/ucs-${version}-\$patch_level/test/ucs-ec2-tools") {
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
        shell(
"""
cfg="examples/jenkins/autotest-10*-app-\${Systemrolle}-\${SambaVersion}.cfg"
sed -i "s|APP_ID|${app.required_apps.join(' ')}|g" \$cfg
sed -i "s|%PARAM_HALT%|\$HALT|g" \$cfg
exec ./ucs-ec2-create -c \$cfg
"""
        )
      }
      // throttle build
      throttleConcurrentBuilds {
        categories(['ec2apptests'])
      }
      configure { project ->
        project / 'properties' / 'hudson.plugins.throttleconcurrents.ThrottleJobProperty' / matrixOptions {
          throttleMatrixBuilds(true)
          throttleMatrixConfigurations(false)
        } 
      }
      // post build
      publishers {
        archiveArtifacts('**/autotest-*.log,**/ucs-test.log,**/updater.log,**/setup.log,**/join.log,**/*.log')
        archiveJunit('**/test-reports/**/*.xml')
      }
    }
  }
}
