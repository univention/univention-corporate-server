description = 'run powershell command'
name = 'run_ps'
args = dict(
	cmd = dict(help='powershell command'),
)

def post(winrm):
	winrm.run(winrm.args.cmd, vars(winrm.args))
