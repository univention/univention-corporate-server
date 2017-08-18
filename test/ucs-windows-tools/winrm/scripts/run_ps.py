description = 'run powershell command'
name = 'run-ps'
args = dict(
	cmd=dict(help='powershell command'),
)


def post(self):
	self.run(self.args.cmd)
