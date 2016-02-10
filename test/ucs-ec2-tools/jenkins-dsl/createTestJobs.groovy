import univention.Constants

import univention.jobs.SambaSelfTest

// Build parameters are exposed as environment variables in Jenkins.
// A seed job build parameter named FOO is available as FOO variable
// in the DSL scripts. See the section about environment variables above.

univention.Constants.VERSIONS.each {

    version = it.getKey()
    patch_level = it.getValue()['patch_level']
    last_version = it.getValue()['last_version']
    path = 'UCS-' + version + '/Tests'

	// ignore 3.2 and 4.0 for now
	if (['4.0', '3.2'].contains(version)) {
		return
	}

    0.upto(patch_level.toInteger()) { level ->
        level = level.toString()
		path = 'UCS-' + version + '/UCS-' + version + '-' + level + '/Specific Tests'
		// create Tests
		folder(path)
		SambaSelfTest.create(this, path, version, level)
	}
}
