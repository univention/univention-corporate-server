from univention.appcenter.actions.docker_remove import Remove
import shutil
import univention.appcenter.docker as docker


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
			self.remove_docker_volumes(app)
			self.remove_docker_images(app)

	def remove_app(self, args):
		super(Purge, self).main(args)

	def remove_apps_files(self, app):
		app_files_dir = '/var/lib/univention-appcenter/apps/{}'.format(app.id)
		try:
			shutil.rmtree(app_files_dir)
		except OSError:
			self.log("WARN: Could not remove '{}'".format(app_files_dir))

	def remove_docker_volumes(self, app):
		for docker_volume in app.docker_volumes:
			host_directory = docker_volume.split(':')[0]
			try:
				shutil.rmtree(host_directory)
			except OSError:
				self.log("WARN: Could not remove docker volume '{}'".format(host_directory))

	def remove_docker_images(self, app):
		returncode = docker.rmi(app.docker_image)
		if returncode != 0:
			self.log("WARN: Could not remove the docker image '{}'".format(app.docker_image))
