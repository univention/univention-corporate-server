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
        choiceParam('release_update', ['public', 'testing', 'none'],
"""
Performs a release update to
<dl>
  <dt>public</dt><dd>the latest publically announced release on http://updates.software-univention.de/</dd>
  <dt>testing</dt><dd>the latest internal release on http://updates-test.software-univention.de</dd>
  <dt>none</dt><dd>perform no update and stay with the initial release</dd>
</dl>""")
		choiceParam('errata_update', ['testing', 'public', 'none'],
"""
Install errata updates from
<dl>
  <dt>testing</dt><dd>the latest internal released errata from http://updates-test.software-univention.de</dd>
  <dt>public</dt><dd>the latest publically announced errata from http://updates.software-univention.de/</dd>
  <dt>none</dt><dd>perform no errata update and stay with the initial release</dd>
</dl>
""")
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
      // wrappers
      wrappers {
        preBuildCleanup()
      }
      // build step
      steps {
        shell(
"""
echo "release_update='\$release_update'" >>examples/jenkins/utils/utils.sh
echo "errata_update='\$errata_update'" >>examples/jenkins/utils/utils.sh
echo "JOB_NAME='\$JOB_NAME'" >>examples/jenkins/utils/utils.sh
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
