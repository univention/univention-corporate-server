package univention.jobs

class SambaSelfTest {
  static create(dslFactory, String path, String version, String patch_level) {
    dslFactory.job(path + '/Samba Self Test') {
      // config
      authenticationToken('secret')
      quietPeriod(60)
      logRotator(-1, 5, -1, -1)
      description("Download samba source package and start samba test suite.")
      concurrentBuild()
      // build parameters
      parameters {
        booleanParam('HALT', true, 'Uncheck to disable shutdown of ec2 instances.')
        stringParam('PATCH_LEVEL', "${patch_level}", "Checkout this patch level version of UCS ${version} ucs-ec2-tools.")
      }
      // svn
      scm {
        svn {
          checkoutStrategy(SvnCheckoutStrategy.CHECKOUT)
          location("svn+ssh://svnsync@billy/var/svn/dev/branches/ucs-${version}/ucs-${version}-\$PATCH_LEVEL/test/ucs-ec2-tools") {
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
exec ./ucs-ec2-create -c examples/jenkins/autotest-500-samba-self-test.cfg
"""
        )
      }
      // post build
      publishers {
        archiveArtifacts('**/autotest-*.log,**/ucs-test.log,**/updater.log,**/setup.log,**/join.log,**/*.log')
        archiveJunit('**/test-reports/**/*.xml')
      }
    }
  }
}
