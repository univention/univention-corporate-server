package univention.jobs

class AppStatusViews {
    static create(dslFactory, String path) {
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
}
