package univention

import javaposse.jobdsl.dsl.Job.matrixJob

// 1. Make a directory at the same level as the DSL called "utilities"
// 2. Make a file called MyUtilities.groovy in the utilities directory
// 3. Put the following contents in it:
//   import javaposse.jobdsl.dsl.Job
//   class MyUtilities {
//     def addEnterpriseFeature(Job job) {
//         job.with {
//           description('Arbitrary feature')
//        }
//     }
//   }
// 4. Then from the DSL, add something like this:
//   import utilities.MyUtilities
//   MyUtilities.addEnterpriseFeature(job)

class Jobs {

	def appAutotestMultiEnv(String path, String version, String patch_level, String app, List roles) {

		def desc = 'App Autotest MultiEnv'
		def name = path + '/' + desc

		matrixJob(name) {
			// config
			quietPeriod(60)
			logRotator(-1, 5, -1, -1)
			description("run ${desc} job for ${app}")
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
				text('Systemrolle', roles)
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
}
