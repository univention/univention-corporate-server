from univention.appcenter.actions.docker_remove import Remove


class Purge(Remove):

	def setup_parser(self, parser):
		super(Purge, self).setup_parser(parser)

	def main(self, args):
		app = args.app
		self.remove_app(args)
		# TODO: remove app's files
		# TODO: remove database
		# TODO: remove database user + credentials-file
		# TODO: remove LDAP users and entries?!
		if app.docker:
			# TODO: remove docker volumes
			# TODO: remove docker images
			pass

	def remove_app(self, args):
		super(Purge, self).main(args)
