ucs-test @ cloud
================

The purpose of this package is to run ucs-test in the cloud, for example Amazon EC2.

Installation
------------
1. Configure S3 bucket "ucs-test-repo" for pushing local \*.deb to S3
	1. Create in region "eu-west-1"
	2. Click "Als Webseite veröffentlichen": <http://ucs-test-repo.s3-website-eu-west-1.amazonaws.com/>
	3. Update permissions:

			{
				"Version":"2008-10-17",
				"Statement":[
					{
						"Sid":"AddPerm",
						"Effect":"Allow",
						"Principal":{
							"AWS":"*"
						},
						"Action":["s3:GetObject"],
						"Resource":["arn:aws:s3:::ucs-test-repo/*"]
					}
				]
			}

2. Configure the jenkins host:
	1. Copy SSH private key to ~/.ssh/$KEYPAIR.pem
	2. Copy the following files to $RESSOURCES/
		* setup-test.py
		* smtp-send.py
		* run-ucs-test.py
	3. Create ~/ucs-test.ini (see example/ucs-test.ini for a template)
		* keypair: $KEYPAIR (your EC2 keypar name)
		* ressources: $RESSOURCES/

3. Jenkins job "Baue aktuelles ucs-test"
	1. cd svn && dpkg-buildpackage -uc -us -b
	2. Pakete zusammenstellen, indizieren

			rm -rf repo
			mkdir repo
			ln *.deb repo/
			dpkg-scanpackages repo | gzip -9 >repo/Packages.gz

	3. Hochladen in S3-Bucket "ucs-test-repo"
		* repo/** → ucs-test-repo/repo

4. Jenkins job "Start ucs-test instances"
	1. Triggered by schedule: "10 1 * * *" (or by previous job)
	2. Execute

			$RESSOURCES/setup-test.py

5. Jenkins job "Collect ucs-test result"
	1. Use script trigger:
		1. every 5 minutes: "*/5 * * * *"
		2. Execute: "$RESSOURCES/imap-get.py --check"
		3. Expect: 0
	2. Execute

			rm -rf test-reports
			exec $RESSOURCES/imap-get.py

	3. Collect JUnit results: "test-reports/1/\*\*/\*.xml"


To-Do
-----
1. Limit maximum runtime of instances
2. Keep-Alive
	* one emails at the end is not sufficient: test results may be lost
	* feed back test is still running
	* error detection when no emails is received (race condition)
3. save state of  instances between reboots
4. description for multiple instances (flok)
	* format
		* shell script?
		* JSON / XML / YAML?
	* control
		* join
		* update
		* execute something other
5. cloud-init as an alternative
	* pass in commands through User-Data
	* should be included in all AMI images


Bugs
----
1. Redirect console output to /dev/hvc0

		ucr set grub/quiet=no grub/bootsplash=nosplash grub/append=console=hvc0 grub/vga=


Euca(lyptus) Tools
------------------
1. Create ~/.eucarc

		EC2_ACCESS_KEY=XXXXXXXXXXXXXXXXXXXX
		EC2_SECRET_KEY=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
		EC2_URL=http://ec2.eu-west-1.amazonaws.com

2. Create $count instances

		# euca-run-instances -n $count -g "SSH and HTTP" -k ph-test -d foo -t t1.micro ami-8dedd5f9
		RESERVATION	r-d6aa8e9f	223093067001	SSH and HTTP
		INSTANCE	i-6748f62f	ami-8dedd5f9			pending	ph-test			2012-06-06T13:52:36.000Z	aki-62695816	None
		INSTANCE	i-7948f631	ami-8dedd5f9			pending	ph-test			2012-06-06T13:52:36.000Z	aki-62695816	None

3. Wait

		# euca-describe-instances
		RESERVATION	r-d6aa8e9f	223093067001	SSH and HTTP
		INSTANCE	i-6748f62f	ami-8dedd5f9	ec2-46-137-6-37.eu-west-1.compute.amazonaws.com	ip-10-228-231-51.eu-west-1.compute.internal	running	ph-test	0	t1.micro	2012-06-06T13:52:36.000Z	eu-west-1b	aki-62695816
		INSTANCE	i-7948f631	ami-8dedd5f9	ec2-176-34-89-10.eu-west-1.compute.amazonaws.com	ip-10-229-78-130.eu-west-1.compute.internal	running	ph-test	1	t1.micro	2012-06-06T13:52:36.000Z	eu-west-1b	aki-62695816
