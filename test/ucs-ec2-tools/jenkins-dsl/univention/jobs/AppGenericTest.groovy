package univention.jobs

class AppGenericTest {
  static create(dslFactory, String path, String version, String patch_level, String last_version) {
    dslFactory.job(path + '/App Generic Test') {
      // config
      authenticationToken('secret')
      quietPeriod(60)
      logRotator(-1, 5, -1, -1)
      description("Start one of the app tests for given Apps.")
      concurrentBuild()
      // build parameters
      parameters {
        booleanParam('HALT', true, 'Uncheck to disable shutdown of ec2 instances.')
        stringParam('PATCH_LEVEL', "${patch_level}", "Checkout this patch level version of UCS ${version} ucs-ec2-tools.")
        stringParam('APP_ID', null, 'Insert the ID of the Apps which should be installed.')
        choiceParam('CFG', [
          "autotest-100-app-master-s3.cfg",
          "autotest-101-app-master-s4.cfg",
          "autotest-102-app-backup-s3.cfg",
          "autotest-103-app-backup-s4.cfg",
          "autotest-104-app-slave-s3.cfg",
          "autotest-105-app-slave-s4.cfg",
          "autotest-106-app-member-s3.cfg",
          "autotest-107-app-member-s4.cfg",
          "autotest-120-appupdate-master-s3.cfg",
          "autotest-121-appupdate-master-s4.cfg",
          "autotest-122-appupdate-backup-s3.cfg",
          "autotest-123-appupdate-backup-s4.cfg",
          "autotest-124-appupdate-slave-s3.cfg",
          "autotest-125-appupdate-slave-s4.cfg",
          "autotest-126-appupdate-member-s3.cfg",
          "autotest-127-appupdate-member-s4.cfg",
          "autotest-110-update-${last_version}-to-${version}-appupdate-master-s3.cfg",
          "autotest-111-update-${last_version}-to-${version}-appupdate-master-s4.cfg",
          "autotest-112-update-${last_version}-to-${version}-appupdate-backup-s3.cfg",
          "autotest-113-update-${last_version}-to-${version}-appupdate-backup-s4.cfg",
          "autotest-114-update-${last_version}-to-${version}-appupdate-slave-s3.cfg",
          "autotest-115-update-${last_version}-to-${version}-appupdate-slave-s4.cfg",
          "autotest-116-update-${last_version}-to-${version}-appupdate-member-s3.cfg",
          "autotest-117-update-${last_version}-to-${version}-appupdate-member-s4.cfg"],
          'Select job configuration.')
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
