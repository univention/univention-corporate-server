/*
 * Copyright 2013 Univention GmbH
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
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/topic",
	"dojo/Deferred",
	"umc/tools",
	"umc/widgets/TitlePane",
	"umc/widgets/Text",
	"umc/widgets/Form",
	"umc/widgets/ContainerWidget",
	"umc/widgets/Page",
	"umc/modules/appcenter/requirements",
	"umc/i18n!umc/modules/appcenter"
], function(declare, lang, array, topic, Deferred, tools, TitlePane, Text, Form, ContainerWidget, Page, requirements, _) {
	return declare("umc.modules.appcenter.AppDetailsDialog", [ Page ], {
		app: null,
		_container: null,

		title: _('App management'),

		reset: function(title) {
			this.set('headerText', title);
			if (this._container) {
				this.removeChild(this._container);
				this._container.destroyRecursive();
			}
			this._container = new ContainerWidget({
				scrollable: true
			});
			this.addChild(this._container);
		},

		showRequirements: function(label, stressedRequirements, appDetailsPage) {
			var opts = {
				appDetailsDialog: this,
				appDetailsPage: appDetailsPage,
				action: this.actionLabel
			};
			var foundRequirements = [];
			tools.forIn(stressedRequirements, lang.hitch(this, function(name, details) {
				var requirement = requirements[name];
				if (requirement) {
					foundRequirements.push([requirement, details]);
				}
			}));
			if (foundRequirements.length) {
				var titlePane = new TitlePane({
					open: true,
					title: label
				});
				array.forEach(foundRequirements, lang.hitch(this, function(foundRequirementArray, i) {
					var foundRequirement = foundRequirementArray[0];
					var details = foundRequirementArray[1];
					var container = new ContainerWidget({});
					container.addChild(new Text({
						content: foundRequirement.toHTML(this.app, details)
					}));
					if (foundRequirement.solution) {
						var buttons = [{
							name: 'solution' + i,
							label: foundRequirement.buttonLabel(this.app, details),
							defaultButton: true,
							callback: function() {
								foundRequirement.solution(opts, this.app, details);
							}
						}];
						container.addChild(new Form({
							buttons: buttons
						}));
					}
					titlePane.addChild(container);
				}));
				this._container.addChild(titlePane);
			}
		},

		showHardRequirements: function(hardRequirements, appDetailsPage) {
			this.showRequirements(_('Continuation is not possible'), hardRequirements, appDetailsPage);
		},

		showSoftRequirements: function(softRequirements, appDetailsPage) {
			this.showRequirements(_('Continuation is not recommended'), softRequirements, appDetailsPage);
		},

		showUp: function(mayContinue, actionLabel) {
			this.actionLabel = actionLabel;
			var deferred = new Deferred();
			var buttons = [{
				name: 'cancel',
				'default': true,
				label: _('Cancel'),
				callback: lang.hitch(this, function() {
					if (mayContinue) {
						topic.publish('/umc/actions', this.moduleID, this.moduleFlavor, this.app.id, 'user-cancel');
					}
					deferred.reject();
				})
			}];
			if (mayContinue) {
				buttons.push({
					name: 'submit',
					label: this.actionLabel,
					callback: function() {
						deferred.resolve();
					}
				});
			}
			this.set('buttons', buttons);
			this.onShowUp();
			deferred.then(lang.hitch(this, 'onBack', true), lang.hitch(this, 'onBack', false));
			return deferred;
		},

		_setButtonsAttr: function(buttons) {
			this._container.addChild(new Form({
				buttons: buttons
			}));
		},

		showErrataHint: function() {
			this._container.addChild(new Text({
				content: _('These changes contain <strong>all package upgrades available</strong> and thus may <strong>include errata updates</strong>. If this is not intended, the corresponding components have to be temporarily deactivated first using the tab "%s" above.', _('Repository Settings')),
				style: {paddingBottom: '.25em'}
			}));
		},

		showUnreachableHint: function(unreachable, masterUnreachable) {
			var componentID = this.app.candidate_component_id || this.app.component_id;
			var label;
			if (this.app.is_master) {
				label = _('The server tried to connect to DC Backups.');
			} else {
				label = _('The server tried to connect to DC Master and DC Backups.');
			}
			label += ' ' + _('The following hosts cannot be reached:');
			this._container.addChild(new Text({
				content: label + '<ul><li>' + unreachable.join('</li><li>') + '</li></ul>'
			}));
			if (!masterUnreachable) {
				var cmdLine = lang.replace('univention-add-app {component_id} -m', {component_id: componentID});
				var commandHint = '<strong>' + _('Attention!') + '</strong>' + ' ' + _('This application requires an extension of the LDAP schema.') + ' ' + _('Be sure to execute the following command as root on all of these backup servers <em>after</em> installing the application.') + '</td></tr><tr><td colspan="2"><pre>' + cmdLine + '</pre>';
				this._container.addChild(new Text({
					content: commandHint
				}));
			}
		},

		packageChangesOne: function(changes, label) {
			var txt = '';
			var details;
			if (changes === undefined || changes.length) {
				if (changes === undefined) {
					details = '<div>' + _('Unknown') + '</div>';
				} else {
					details = '<ul><li>' + changes.join('</li><li>') + '</li></ul>';
				}
				txt = '<p>' + label + details + '</p>';
			}
			return txt;
		},

		showPackageChanges: function(install, remove, broken, incompatible, opened, host) {
			var txt = '';
			txt += this.packageChangesOne(install, _('The following packages will be installed or upgraded:'));
			txt += this.packageChangesOne(remove, _('The following packages will be removed:'));
			txt += this.packageChangesOne(broken, _('This operation causes problems in the following packages that cannot be resolved:'));
			if (txt === '') {
				txt = '<p>' + _('No changes') + '</p>';
			}
			if (incompatible) {
				txt += '<div>' + _('The version of the remote App Center is <strong>incompatible</strong> with the local one. Please update your hosts.') + '</div>';
			}
			var install_count = install ? install.length : _('Unknown');
			var remove_count = remove ? (remove.length === 0 ? 0 : '<strong>' + remove.length + '</strong>') : _('Unknown');
			var broken_count = broken ? (broken.length === 0 ? 0 : '<strong>' + broken.length + '</strong>') : _('Unknown');
			var incompatible_headline = incompatible ? ', <strong>' + _('incompatible') : '</strong>';
			this._container.addChild(TitlePane({
				title: _('Software changes on %(host)s (installed/upgraded: %(installed)s, removed: %(removed)s, erroneous: %(erroneous)s%(incompatible)s)', {host: host, installed: install_count, removed: remove_count, erroneous: broken_count, incompatible: incompatible_headline}),
				open: opened,
				content: txt
			}));
		},

		onShowUp: function() {
		},

		onBack: function(continued) {
		}

	});
});

