/*
 * Copyright 2013-2015 Univention GmbH
 *
 * http://www.univention.de/
 *
 * All rights reserved.
 *
 * The source code of this program is made available
 * under the terms of the GNU Affero General Public License version 3
 * (GNU AGPL V3) as published by the Free Software Foundation.
 *
 * Binary versions of this program provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention and not subject to the GNU AGPL V3.
 *
 * In the case you use this program under the terms of the GNU AGPL V3,
 * the program is provided in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public
 * License with the Debian GNU/Linux or Univention distribution in file
 * /usr/share/common-licenses/AGPL-3; if not, see
 * <http://www.gnu.org/licenses/>.
 */
/*global define*/

define([
	"dojo/_base/kernel",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/topic",
	"umc/i18n!umc/modules/appcenter"
], function(kernel, lang, array, topic, _) {
	var Requirement = function(args) {
		this.reasonDescription = args.reasonDescription;
		this.solutionDescription = args.solutionDescription;
		this.solutionLabel = args.solutionLabel;
		this.solution = args.solution;
		this.stayAfterSolution = args.stayAfterSolution;
	};

	kernel.extend(Requirement, {
		_makeDetails: function(app, details) {
			if (!details) {
				details = {};
			}
			if (typeof details === 'string' || details instanceof Array) {
				details = {detail: details};
			}
			return lang.mixin({}, app, details);
		},

		_renderReason: function(app, details) {
			return this.reasonDescription(this._makeDetails(app, details));
		},

		_renderSolution: function(app, details) {
			if (this.solutionDescription) {
				return this.solutionDescription(this._makeDetails(app, details));
			} else {
				return '';
			}
		},

		buttonLabel: function(app, details) {
			return this.solutionLabel(this._makeDetails(app, details));
		},

		toHTML: function(app, details) {
			return '<p>' + this._renderReason(app, details) + ' ' + this._renderSolution(app, details) + '</p>';
		}
	});

	return {
		Requirement: Requirement,
		must_not_have_concurrent_operation: new Requirement({
			reasonDescription: function() {
				return _('Another package operation is in progress.');
			},
			solutionDescription: function() {
				return _('Wait for that operation to finish.');
			},
			solutionLabel: function() {
				return _('Show progress');
			},
			solution: function(opts) {
				opts.appDetailsPage.standbyDuring(opts.appDetailsPage.switchToProgressBar(), opts.appDetailsPage._progressBar);
			}
		}),
		must_have_fitting_ucs_version: new Requirement({
			reasonDescription: function(details) {
				return _('The application requires UCS version %(required_version)s or later.', details);
			},
			solutionDescription: function() {
				return _('The system has to be updated.');
			},
			solutionLabel: function() {
				return _('Open Software update Module');
			},
			solution: function() {
				topic.publish('/umc/modules/open', 'updater');
			}
		}),
		must_have_valid_license: new Requirement({
			reasonDescription: function() {
				return _('For the installation of this application, a UCS license key with a key identification (Key ID) is required.');
			},
			solutionDescription: function() {
				return _('You receive such a license key within a couple of minutes via email after a free activation.');
			},
			solutionLabel: function() {
				return _('Activate UCS now');
			},
			solution: function(opts) {
				opts.appDetailsPage.showLicenseRequest(opts.action);
			}
		}),
		must_have_candidate: new Requirement({
			reasonDescription: function(details) {
				return _('%s cannot be updated. The application is either not installed or no newer version is available.', details.name);
			}
		}),
		must_not_be_installed: new Requirement({
			reasonDescription: function(details) {
				return _('%s is already installed.', details.name);
			}
		}),
		must_not_be_end_of_life: new Requirement({
			reasonDescription: function(details) {
				return _('%s was discontinued and may not be installed anymore.', details.name);
			}
		}),
		must_have_supported_architecture: new Requirement({
			reasonDescription: function(details) {
				return _('%(name)s only supports %(supported)s as architecture. %(msg)s', details);
			}
		}),
		must_be_joined_if_master_packages: new Requirement({
			reasonDescription: function() {
				return _('This application requires an extension of the LDAP schema.');
			},
			solutionDescription: function() {
				return _('The system has to join a domain before the application can be installed!');
			},
			solutionLabel: function() {
				return _('Open Domain Join Module');
			},
			solution: function() {
				topic.publish('/umc/modules/open', 'join');
			}
		}),
		must_have_correct_server_role: new Requirement({
			reasonDescription: function(details) {
				return _('%(name)s cannot be installed on the current server role (%(current_role)s). In order to install the application, one of the following roles is necessary: %(allowed_roles)s', details);
			}
		}),
		must_have_no_unmet_dependencies: new Requirement({
			reasonDescription: function(details) {
				var txt = _('%s requires the following applications.', details.name);
				txt += '<ul><li>' + array.map(details.detail, function(app) { return app.name; }).join('</li><li>') + '</li></ul>';
				return txt;
			},
			solutionDescription: function() {
				return _('Install them first.');
			},
			solutionLabel: function(details) {
				return _('Open %s', details.detail[0].name);
			},
			solution: function(opts, details) {
				opts.appDetailsPage.set('app', details[0]);
				return opts.appDetailsPage.appLoadingDeferred;
			}
		}),
		must_have_no_conflicts_packages: new Requirement({
			reasonDescription: function(details) {
				var txt = _('%s conflicts with the following packages.', details.name);
				txt += '<ul><li>' + details.detail.join('</li><li>') + '</li></ul>';
				return txt;
			},
			solutionDescription: function() {
				return _('Uninstall them first.');
			}
		}),
		must_have_no_conflicts_apps: new Requirement({
			reasonDescription: function(details) {
				var txt = _('%s conflicts with the following applications.', details.name);
				txt += '<ul><li>' + array.map(details.detail, function(app) { return app.name; }).join('</li><li>') + '</li></ul>';
				return txt;
			},
			solutionDescription: function() {
				return _('Uninstall them first.');
			},
			solutionLabel: function(details) {
				return _('Open %s', details.detail[0].name);
			},
			solution: function(opts, details) {
				opts.appDetailsPage.set('app', details[0]);
				return opts.appDetailsPage.appLoadingDeferred;
			}
		}),
		must_not_be_depended_on: new Requirement({
			reasonDescription: function(details) {
				var txt = _('%s is required for the following applications to work.', details.name);
				txt += '<ul><li>' + array.map(details.detail, function(app) { return app.name; }).join('</li><li>') + '</li></ul>';
				return txt;
			},
			solutionDescription: function() {
				return _('Uninstall them first.');
			},
			solutionLabel: function(details) {
				return _('Open %s', details.detail[0].name);
			},
			solution: function(opts, details) {
				opts.appDetailsPage.set('app', details[0]);
				return opts.appDetailsPage.appLoadingDeferred;
			}
		}),
		shall_only_be_installed_in_ad_env_with_password_service: new Requirement({
			stayAfterSolution: true,
			reasonDescription: function() {
				return _('The application requires the password service to be set up on the Active Directory domain controller server.');
			},
			solutionDescription: function() {
				return _('The steps how to install the service on that machine are described in the online documentation.');
			},
			solutionLabel: function() {
				return _('Open the documentation');
			},
			solution: function() {
				window.open(_('https://docs.univention.de/manual.html#ad-connector:password-dienst'));
			}
		}),
		shall_have_enough_ram: new Requirement({
			reasonDescription: function(details) {
				return _('The application requires %(minimum)d MB of free RAM but only %(current)d MB are available.', details);
			}
		})
	};
});

