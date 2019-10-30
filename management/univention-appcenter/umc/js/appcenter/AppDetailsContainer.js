/*
 * Copyright 2013-2019 Univention GmbH
 *
 * https://www.univention.de/
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
 * <https://www.gnu.org/licenses/>.
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/when",
	"dojox/html/entities",
	"umc/tools",
	"umc/widgets/ContainerWidget",
	"umc/widgets/TitlePane",
	"umc/widgets/Text",
	"umc/widgets/Button",
	"./AppSettings",
	"./requirements",
	"umc/i18n!umc/modules/appcenter"
], function(declare, lang, array, when, entities, tools, ContainerWidget, TitlePane, Text, Button, AppSettings, requirements, _) {
	return declare("umc.modules.appcenter.AppDetailsContainer", [ ContainerWidget ], {
		configForm: null,

		funcName: '',
		funcLabel: '',
		app: null,
		details: null,
		appDetailsPage: null,
		mayShowAppSettings: false,
		doesShowSomething: false,

		standbyDuring: null, // TODO

		buildRendering: function() {
			this.inherited(arguments);

			this.showConfiguration();
			this.showHardRequirements();
			this.showSoftRequirements();
			this.showPackageRelated();
		},

		showConfiguration: function() {
			if (!this.mayShowAppSettings) {
				return;
			}
			if (this.details.serious_problems) {
				return;
			}

			var funcName = this.funcName;
			if (funcName == 'install') {
				funcName = 'Install';
			} else if (funcName == 'update') {
				funcName = 'Upgrade';
			} else if (funcName == 'uninstall') {
				funcName = 'Remove';
			}
			this.standbyDuring(tools.umcpCommand('appcenter/config', {app: this.app.id, phase: funcName}).then(lang.hitch(this, function(data) {
				var form = AppSettings.getForm(this.app, data.result.values, funcName, false);
				if (form) {
					this.configForm = form;
					this.doesShowSomething = true;
					this.addChild(this.configForm);
				}
			})));
		},

		showRequirements: function(label, stressedRequirements, appDetailsPage) {
			var opts = {
				appDetailsPage: appDetailsPage
			};
			var foundRequirements = [];
			tools.forIn(stressedRequirements, function(name, details) {
				var requirement = requirements[name];
				if (requirement) {
					foundRequirements.push([requirement, details]);
				}
			});
			if (foundRequirements.length) {
				var container = new ContainerWidget({});
				array.forEach(foundRequirements, lang.hitch(this, function(foundRequirementArray, i) {
					var foundRequirement = foundRequirementArray[0];
					var details = foundRequirementArray[1];
					this.doesShowSomething = true;
					container.addChild(new Text({
						content: '<hr/>'
					}));
					this.doesShowSomething = true;
					container.addChild(new Text({
						content: foundRequirement.toHTML(this.app, details)
					}));
					if (foundRequirement.solution) {
						var label = foundRequirement.buttonLabel(this.app, details);
						if (label) {
							this.doesShowSomething = true;
							container.addChild(new Button({
								name: 'solution' + i,
								label: label,
								callback: lang.hitch(this, function() {
									opts.action = this.funcLabel;
									var deferred = foundRequirement.solution(opts, details);
									if (!foundRequirement.stayAfterSolution) {
										when(deferred).always(lang.hitch(this, 'onBack', false));
									}
								})
							}));
						}
					}
				}));
				this.doesShowSomething = true;
				this.addChild(container);
			}
		},

		showHardRequirements: function() {
			this.showRequirements(_("It is not possible to continue"), this.details.invokation_forbidden_details, this.appDetailsPage);
		},

		showSoftRequirements: function() {
			this.showRequirements(_("It is not recommended to continue"), this.details.invokation_warning_details, this.appDetailsPage);
		},

		showPackageRelated: function() {
			if (!this.details.software_changes_computed) {
				return;
			}

			this.showUnreachableHint();
			this.showErrataHint();
			this.showPackageChanges();
		},

		showUnreachableHint: function() {
			if (!this.details.unreachable.length) {
				return;
			}

			var componentID = this.app.candidateComponentID || this.app.componentID;
			var label = _('The server tried to connect to the involved systems.') + ' ' + _('The following hosts cannot be reached or do not have access to the App Center server:');
			this.doesShowSomething = true;
			this.addChild(new Text({
				content: label + '<ul><li>' + array.map(this.details.unreachable, function(v) { return entities.encode(v); }).join('</li><li>') + '</li></ul>'
			}));
			if (!this.details.masterUnreachable) {
				var cmdLine = lang.replace('univention-app install {app_id} --only-master-packages', {app_id: entities.encode(this.app.id)});
				var commandHint = '<strong>' + _('Attention!') + '</strong>' + ' ' + _('This application requires an extension of the LDAP schema.') + ' ' + _('Be sure to execute the following command as root on all of these backup servers <em>after</em> installing the application.') + '</td></tr><tr><td colspan="2"><pre>' + cmdLine + '</pre>';
				this.doesShowSomething = true;
				this.addChild(new Text({
					content: commandHint
				}));
			}
		},

		showErrataHint: function() {
			if (this.funcName !== 'update') {
				return;
			}

			var repositoryButton = lang.replace('<a href="javascript:void(0)" onclick="require(\'umc/app\').openModule(\'appcenter\', \'components\')">{name}</a>', {name: _('Repository Settings')});
			this.doesShowSomething = true;
			this.addChild(new Text({
				content: _('These changes contain <strong>all package upgrades available</strong> and thus may <strong>include errata updates</strong>. If this is not intended, the corresponding components have to be temporarily deactivated first using the tab "%s" in the App Center.', repositoryButton),
				style: {paddingBottom: '.25em'}
			}));
		},

		showPackageChanges: function() {
			var noHostInfo = tools.isEqual({}, this.details.hosts_info);
			this._showPackageChanges(this.details.install, this.details.remove, this.details.broken, false, noHostInfo, this.host);
			tools.forIn(this.details.hosts_info, lang.hitch(this, function(host, host_info) {
				this._showPackageChanges(host_info.result.install, host_info.result.remove, host_info.result.broken, !host_info.compatible_version, false, host);
			}));
		},

		_showPackageChanges: function(install, remove, broken, incompatible, opened, host) {
			var _packageChangesList = function(changes, label) {
				var txt = '';
				var details;
				if (changes === undefined || changes.length) {
					if (changes === undefined) {
						details = '<div>' + _('Unknown') + '</div>';
					} else {
						details = '<ul><li>' + array.map(changes, function(v) { return entities.encode(v); }).join('</li><li>') + '</li></ul>';
					}
					txt = '<p>' + label + details + '</p>';
				}
				return txt;
			};

			var _packageChangeLabel = function(changes, labelSingular, labelPlural, resultList) {
				if (!changes) {
					resultList.push(lang.replace(labelPlural, [_('an unknown amount of')]));
				}
				else if (changes.length === 1) {
					resultList.push(labelSingular);
				}
				else if (changes.length > 1) {
					resultList.push(lang.replace(labelPlural, [changes.length]));
				}
			};

			if (incompatible) {
				this.doesShowSomething = true;
				this.addChild(new Text({
					content: '<p>' + _('The version of the remote App Center is <strong>incompatible</strong> with the local one. Please update your hosts.') + '</p>'
				}));
			}

			var changeLabels = [];
			_packageChangeLabel(install, _('1 package will be installed / upgraded'), _('{0} packages will be installed / upgraded'), changeLabels);
			_packageChangeLabel(remove, '<strong>' + _('1 package will be removed') + '</strong>', '<strong>' + _('{0} packages will be removed') + '</strong>', changeLabels);
			_packageChangeLabel(broken, '<strong>' + _('1 package is erroneous') + '</strong>', '<strong>' + _('{0} packages are erroneous') + '</strong>', changeLabels);
			if (!changeLabels.length) {
				changeLabels = '<p>' + _('No software changes on %s necessary.', host || _('this host')) + '</p>';
			} else {
				changeLabels = '<p>' + _('The following software changes on %s will be applied: ', host || _('this host')) + changeLabels.join(', ') + '</p>';
			}
			this.doesShowSomething = true;
			this.addChild(new Text({
				content: changeLabels
			}));

			var txt = '';
			txt += _packageChangesList(install, _('The following packages will be installed or upgraded:'));
			txt += _packageChangesList(remove, _('The following packages will be removed:'));
			txt += _packageChangesList(broken, _('This operation causes problems in the following packages that cannot be resolved:'));
			if (txt === '') {
				txt = '<p>' + _('No software changes necessary.') + '</p>';
			}
			this.doesShowSomething = true;
			this.addChild(new TitlePane({
				'class': 'umcAppMoreTitlePane',
				title: _('More information...'),
				open: false,
				content: txt
			}));
		}
	});
});


