package univention.jobs

class AppGenericTest {
  static create(dslFactory, String path, String version, String patch_level, String last_version) {
    dslFactory.Job(path + '/App Generic Test') {
      // config
      authenticationToken('secret')
      quietPeriod(60)
      logRotator(-1, 5, -1, -1)
      description("Start one of the app tests for given Apps.")
      concurrentBuild()
      // build parameters
      parameters {
        booleanParam('HALT', true, 'Uncheck to disable shutdown of ec2 instances.')
        stringParam('patch_level', "${patch_level}", "Checkout this patch level version of UCS ${version} ucs-ec2-tools.")
        stringParam('APP_ID', null, 'Insert the ID of the Apps which should be installed.')
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
      // wrappers
      wrappers {
        preBuildCleanup()
      }
      // build step
      steps {
        shell(
"""
cfg="examples/jenkins/\$CFG"
sed -i "s|APP_ID|\$APP_ID|g" \$cfg
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
