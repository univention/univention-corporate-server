description = 'wait for client with timeout'
name = 'wait_for_client'
args = dict(
	timeout=dict(help='timeout', default=180, type=int),
)


def post(self):
	self.wait_for_client(timeout=self.args.timeout)
