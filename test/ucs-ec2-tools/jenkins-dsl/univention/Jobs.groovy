package univention

class Jobs {

  static createAppStatusViews(dslFactory, String path) {
      // stable
      dslFactory.listView(path + '/Stable') {
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
      dslFactory.listView(path + '/Failed') {
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
      dslFactory.listView(path + '/Running') {
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

  static createAppAutotestUpdateMultiEnv(dslFactory, String path, String version, String patch_level, Map app) {
    def desc = 'App Autotest Update MultiEnv'
    def job_name = path + '/' + desc
    dslFactory.matrixJob(job_name) {
      // config
      authenticationToken('secret')
      quietPeriod(60)
      logRotator(-1, 5, -1, -1)
      description("run ${desc} for ${app.id}")
      concurrentBuild()
      // build parameters
      parameters {
        booleanParam('HALT', true, 'uncheck to disable shutdown of ec2 instances')
        booleanParam('Update_to_testing_errata_updates', false, 'Update to unreleased errata updates from updates-test.software-univention.de?')
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
cfg="examples/jenkins/autotest-12*-appupdate-\${Systemrolle}-\${SambaVersion}.cfg"
sed -i "s|APP_ID|${app.required_apps.join(' ')}|g" \$cfg
test "\$Update_to_testing_errata_updates" = true && sed -i "s|upgrade_to_latest_errata|upgrade_to_latest_test_errata|g" \$cfg
exec ./ucs-ec2-create -c \$cfg
          """
        )
      }
      // throttle build
      throttleConcurrentBuilds {
        categories(['ec2apptests'])
        //configure { matrixOptions ->
        //   matrixOptions {
        //     throttleMatrixBuilds('true')
        //     throttleMatrixConfigurations('false')
        //   }
        //}
      }
      // post build
      publishers {
        archiveArtifacts('**/autotest-*.log,**/ucs-test.log,**/updater.log,**/setup.log,**/join.log,**/*.log')
        archiveJunit('**/test-reports/**/*.xml')
      }
    }
  }

  static createAppAutotestMultiEnv(dslFactory, String path, String version, String patch_level, Map app) {
    def desc = 'App Autotest MultiEnv'
    def job_name = path + '/' + desc
    dslFactory.matrixJob(job_name) {
      // config
      authenticationToken('secret')
      quietPeriod(60)
      logRotator(-1, 5, -1, -1)
      description("run ${desc} for ${app.id}")
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
        //configure { matrixOptions ->
        //   matrixOptions {
        //     throttleMatrixBuilds('true')
        //     throttleMatrixConfigurations('false')
        //   }
        //}
      }
      // post build
      publishers {
        archiveArtifacts('**/autotest-*.log,**/ucs-test.log,**/updater.log,**/setup.log,**/join.log,**/*.log')
        archiveJunit('**/test-reports/**/*.xml')
      }
    }
  }

  static createAppAutotestMultiEnvUpdateFrom(dslFactory, String path, String version, String patch_level, String last_version, Map app) {
    def desc = "App Autotest MultiEnv Release Update"
    def job_name = path + '/' + desc
    dslFactory.matrixJob(job_name) {
      // config
      quietPeriod(60)
      authenticationToken('secret')
      logRotator(-1, 5, -1, -1)
      description("run ${desc} for ${app.id} (update from ${last_version} to ${version})")
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
cfg="examples/jenkins/autotest-11*-update-${last_version}-to-${version}-appupdate-\${Systemrolle}-\${SambaVersion}.cfg"
sed -i "s|APP_ID|${app.required_apps.join(' ')}|g" \$cfg
sed -i "s|%PARAM_HALT%|\$HALT|g" \$cfg
exec ./ucs-ec2-create -c \$cfg
"""
        )
      }
      // throttle build
      throttleConcurrentBuilds {
        categories(['ec2apptests'])
        configure { project ->
          project / 'properties' / 'hudson.plugins.throttleconcurrents.ThrottleJobProperty' << matrixOptions {
            throttleMatrixBuilds(true)
            throttleMatrixConfigurations(false)
          }
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
