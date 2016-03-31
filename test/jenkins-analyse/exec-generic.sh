python ./jenkins-analyse/jenkins_analyze_html.py -u http://jenkins.knut.univention.de:8080/job/UCS-4.1/job/UCS-4.1-1/job/Autotest%20MultiEnv%20%28IPv6%29%204.1%20Generic/ -l -o build.html
python - "$1" "$2" "$3" <<END
import sys
import jenkinsapi.jenkins

systemrolleMaster = sys.argv[1]
systemrolleElse = sys.argv[2]
url = sys.argv[3]
j = jenkinsapi.jenkins.Jenkins(url)
job = j.get_job('Autotest MultiEnv (IPv6) 4.1 Generic')
build = job.get_build(job.get_last_buildnumber())

for build_item in list(build.get_matrix_runs()):
	name = build_item.name
	if systemrolleMaster in name and systemrolleElse in name:
		if "paramiko" in  build_item.get_console():
			fw = open('paramiko-error.txt','w')
			fw.write('Paramiko-Error was thrown during build')
		else:
			fw = open('no-paramiko-error.txt','w')
			fw.write('No Paramiko-Error was thrown during build')
	

END
