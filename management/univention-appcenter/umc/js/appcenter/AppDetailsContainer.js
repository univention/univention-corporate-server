/*
 * Copyright 2020-2022 Univention GmbH
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
	"./requirements",
	"umc/i18n!umc/modules/appcenter"
], function(declare, lang, array, when, entities, tools, ContainerWidget, TitlePane, Text, Button, requirements, _) {
	return declare("umc.modules.appcenter.AppDetailsContainer", [ ContainerWidget ], {
		// these properties have to be provided
		funcName: '',
		funcLabel: '',
		app: null,
		details: null,
		host: null,
		appDetailsPage: null,
		//
		showWarnings: true,
		showNonWarnings: true,

		doesShowSomething: false,
		doesShowWarnings: false,

		buildRendering: function() {
			this.inherited(arguments);

			var showUnreachableHint = this.details.software_changes_computed && this.details.unreachable.length;
			var unreachableHintIsHard = showUnreachableHint && this.details.master_unreachable;
			var showErrataHint = this.details.software_changes_computed && this.funcName === 'update';
			var packageChanges = [];
			if (this.details.software_changes_computed) {
				packageChanges.push({
					install: this.details.install,
					remove: this.details.remove,
					broken: this.details.broken,
					incompatible: false,
					host: this.host
				});
				tools.forIn(this.details.hosts_info, function(host, host_info) {
					packageChanges.push({
						install: host_info.result.install,
						remove: host_info.result.remove,
						broken: host_info.result.broken,
						incompatible: !host_info.compatible_version,
						host: host
					});
				});
			}
			var brokenPackageChanges = packageChanges.filter(function(changes) {
				return !!changes.broken.length || changes.incompatible;
			});
			var nonBrokenPackageChanges = packageChanges.filter(function(changes) {
				return !changes.broken.length && !changes.incompatible;
			});

			if (this.showWarnings) {
				// hard warnings
				this.showHardRequirements(this.details.invokation_forbidden_details, this.appDetailsPage);
				if (showUnreachableHint && unreachableHintIsHard) {
					this.showUnreachableHint(this.details.unreachable, this.details.master_unreachable);
				}
				array.forEach(brokenPackageChanges, lang.hitch(this, function(changes) {
					this.showPackageChanges(changes.install, changes.remove, changes.broken, changes.incompatible, changes.host);
				}));

				// soft warnings
				if (showUnreachableHint && !unreachableHintIsHard) {
					this.showUnreachableHint(this.details.unreachable, this.details.master_unreachable);
				}
				this.showSoftRequirements(this.details.invokation_warning_details, this.appDetailsPage);
				if (showErrataHint) {
					this.showErrataHint();
				}
			}

			if (this.showNonWarnings) {
				// non warnings
				array.forEach(nonBrokenPackageChanges, lang.hitch(this, function(changes) {
					this.showPackageChanges(changes.install, changes.remove, changes.broken, changes.incompatible, changes.host);
				}));
			}
		},

		addChild: function() {
			this.doesShowSomething = true;
			this.inherited(arguments);
		},

		showRequirements: function(label, stressedRequirements, appDetailsPage, isHardRequirement) {
			var opts = {
				appDetailsPage: appDetailsPage
			};
			var foundRequirements = [];
			tools.forIn(stressedRequirements, lang.hitch(this, function(name, details) {
				var requirement = requirements[name];
				if (requirement) {
					foundRequirements.push([requirement, details]);
				}
			}));
			if (foundRequirements.length) {
				var container = new ContainerWidget({});
				array.forEach(foundRequirements, lang.hitch(this, function(foundRequirementArray, i) {
					var foundRequirement = foundRequirementArray[0];
					var details = foundRequirementArray[1];
					var content = [];
					content.push(new Text({
						content: foundRequirement.toHTML(this.app, details)
					}));
					if (foundRequirement.solution) {
						var label = foundRequirement.buttonLabel(this.app, details);
						if (label) {
							content.push(new Button({
								name: 'solution' + i,
								label: label,
								callback: lang.hitch(this, function() {
									opts.action = this.funcLabel;
									var deferred = foundRequirement.solution(opts, details);
									when(deferred).always(lang.hitch(this, 'onSolutionClicked', foundRequirement.stayAfterSolution));
								})
							}));
						}
					}
					this.addContent(container, content, true, isHardRequirement);
				}));
				this.addChild(container);
				if (!isHardRequirement) {
					this.doesShowWarnings = true;
				}
			}
		},

		showHardRequirements: function(hardRequirements, appDetailsPage) {
			this.showRequirements(_("It is not possible to continue"), hardRequirements, appDetailsPage, true);
		},

		showSoftRequirements: function(softRequirements, appDetailsPage) {
			this.showRequirements(_("It is not recommended to continue"), softRequirements, appDetailsPage, false);
		},

		showErrataHint: function() {
			var repositoryButton = lang.replace('<a href="javascript:void(0)" onclick="require(\'umc/app\').openModule(\'appcenter\', \'components\')">{name}</a>', {name: _('Repository Settings')});
			var text = new Text({
				content: _('These changes contain <strong>all package upgrades available</strong> and thus may <strong>include errata updates</strong>. If this is not intended, the corresponding components have to be temporarily deactivated first using the tab "%s" in the App Center.', repositoryButton)
			});
			this.addContent(this, [text], true, false);
			this.doesShowWarnings = true;
		},

		showUnreachableHint: function(unreachable, masterUnreachable) {
			var componentID = this.app.candidateComponentID || this.app.componentID;

			var content = [];
			var label = _('The server tried to connect to the involved systems.') + ' ' + _('The following hosts cannot be reached or do not have access to the App Center server:');
			content.push(new Text({
				content: label + '<ul><li>' + array.map(unreachable, function(v) { return entities.encode(v); }).join('</li><li>') + '</li></ul>'
			}));
			if (!masterUnreachable) {
				var cmdLine = lang.replace('univention-app install {app_id} --only-master-packages', {app_id: entities.encode(this.app.id)});
				var commandHint = '<strong>' + _('Attention!') + '</strong>' + ' ' + _('This application requires an extension of the LDAP schema.') + ' ' + _('Be sure to execute the following command as root on all of these backup servers <em>after</em> installing the application.') + '</td></tr><tr><td colspan="2"><pre>' + cmdLine + '</pre>';
				content.push(new Text({
					content: commandHint
				}));
				this.doesShowWarnings = true;
			}
			this.addContent(this, content, true, masterUnreachable);
		},

		showPackageChanges: function(install, remove, broken, incompatible, host) {
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

			var content = [];

			if (incompatible) {
				content.push(new Text({
					content: '<p>' + _('The version of the remote App Center is <strong>incompatible</strong> with the local one. Please update your hosts.') + '</p>'
				}));
			}

			var changeLabels = [];
			_packageChangeLabel(install, _('1 package will be installed / upgraded'), _('{0} packages will be installed / upgraded'), changeLabels);
			_packageChangeLabel(remove, '<strong>' + _('1 package will be removed') + '</strong>', '<strong>' + _('{0} packages will be removed') + '</strong>', changeLabels);
			_packageChangeLabel(broken, '<strong>' + _('1 package is erroneous') + '</strong>', '<strong>' + _('{0} packages are erroneous') + '</strong>', changeLabels);
			if (!changeLabels.length) {
				changeLabels = _('No software changes on %s necessary.', host || _('this host'));
			} else {
				changeLabels = _('The following software changes on %s will be applied: ', host || _('this host')) + changeLabels.join(', ');
			}
			content.push(new Text({
				content: changeLabels
			}));

			var txt = '';
			txt += _packageChangesList(install, _('The following packages will be installed or upgraded:'));
			txt += _packageChangesList(remove, _('The following packages will be removed:'));
			txt += _packageChangesList(broken, _('This operation causes problems in the following packages that cannot be resolved:'));
			if (txt === '') {
				txt = '<p>' + _('No software changes necessary.') + '</p>';
			}
			content.push(new TitlePane({
				'class': 'umcAppMoreTitlePane',
				title: _('More information...'),
				open: false,
				content: txt
			}));
			var isWarning = !!broken.length || incompatible;
			this.addContent(this, content, isWarning, isWarning);
		},

		addContent: function(parent, content, isWarning, isHardWarning) {
			var _class = '';
			if (isWarning) {
				_class = 'AppDetailsDialog__warning';

				if (isHardWarning) {
					_class += ' AppDetailsDialog__warning--hard';
				} else {
					_class += ' AppDetailsDialog__warning--soft';
				}
			}
			var outer = new ContainerWidget({
				'class': _class
			});
			var inner = new ContainerWidget({});

			array.forEach(content, function(c) {
				inner.addChild(c);
			});

			outer.addChild(inner);
			parent.addChild(outer);
		},

		onSolutionClicked: function(stayAfterSolution) {
			// event stub
		}
	});
});



