
import univention.config_registry
import subprocess

def createMachinePassword():
	"""
	Returns a $(pwgen) generated password according to the 
	requirements in
		machine/password/length
		machine/password/complexity
	"""
	ucr = univention.config_registry.ConfigRegistry()
	ucr.load()
	length = ucr.get('machine/password/length', '20')
	compl = ucr.get('machine/password/complexity', 'scn')
	p = subprocess.Popen(["pwgen", "-1", "-" + compl, length], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	(stdout, stderr) = p.communicate()
	return stdout.strip()
