from univention.appcenter.actions.docker_remove import Remove
import shutil


class Purge(Remove):

	def setup_parser(self, parser):
		super(Purge, self).setup_parser(parser)

	def main(self, args):
		app = args.app
		self.remove_app(args)
		self.remove_apps_files(app)
		# TODO: remove database
		# TODO: remove database user + credentials-file
		# TODO: remove LDAP users and entries?!
		if app.docker:
			# TODO: remove docker volumes
			# TODO: remove docker images
			pass

	def remove_app(self, args):
		super(Purge, self).main(args)

	def remove_apps_files(self, app):
		app_files_dir = '/var/lib/univention-appcenter/apps/{}'.format(app.id)
		try:
			shutil.rmtree(app_files_dir)
		except OSError:
			self.log("WARN: Could not remove '{}'".format(app_files_dir))
