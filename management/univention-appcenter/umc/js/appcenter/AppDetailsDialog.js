/*
 * Copyright 2013-2016 Univention GmbH
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
	"dojox/html/entities",
	"dojo/topic",
	"dojo/when",
	"dojo/Deferred",
	"umc/tools",
	"umc/widgets/TitlePane",
	"umc/widgets/Button",
	"umc/widgets/Text",
	"umc/widgets/TextBox",
	"umc/widgets/CheckBox",
	"umc/widgets/ComboBox",
	"umc/widgets/Form",
	"umc/widgets/ContainerWidget",
	"umc/widgets/Page",
	"umc/modules/appcenter/requirements",
	"./_AppDialogMixin",
	"umc/i18n!umc/modules/appcenter"
], function(declare, lang, array, entities, topic, when, Deferred, tools, TitlePane, Button, Text, TextBox, CheckBox, ComboBox, Form, ContainerWidget, Page, requirements, _AppDialogMixin, _) {
	return declare("umc.modules.appcenter.AppDetailsDialog", [ Page, _AppDialogMixin ], {
		_container: null,
		_continueDeferred: null,
		_configForm: null,
		_confirmForm: null,

		title: _('App management'),

		reset: function(mayContinue, title, text, actionLabel) {
			this._clearWidget('_configForm', false);
			this._clearWidget('_container', true);
			this._clearWidget('_confirmForm', true);

			if (this._continueDeferred) {
				this._continueDeferred.reject();
			}
			this._continueDeferred = new Deferred();

			this.set('headerText', title);
			this.set('helpText', text);

			this.actionLabel = actionLabel;
			var close = lang.hitch(this, function() {
				if (mayContinue) {
					topic.publish('/umc/actions', this.moduleID, this.moduleFlavor, this.app.id, 'user-cancel');
				}
				this._continueDeferred.reject();
			});

			this.set('headerButtons', [{
				name: 'close',
				iconClass: 'umcCloseIconWhite',
				label: _('Cancel installation'),
				callback: close
			}]);

			var buttons = [{
				name: 'cancel',
				'default': true,
				label: _('Cancel'),
				callback: close
			}];
			if (mayContinue) {
				buttons.push({
					name: 'submit',
					label: this.actionLabel,
					callback: lang.hitch(this, function() {
						var values = null;
						if (this._configForm) {
							values = this._configForm.get('value');
						}
						this._continueDeferred.resolve(values);
					})
				});
			}

			this._continueDeferred.then(lang.hitch(this, 'onBack', true), lang.hitch(this, 'onBack', false));
			this._container = new ContainerWidget({});
			this.addChild(this._container);

			this._confirmForm = new Form({
				buttons: buttons,
				style: 'margin-top: 1.5em;'
			});
			this.addChild(this._confirmForm);
		},

		showConfiguration: function(funcName) {
			var widgets = [];
			if (funcName == 'install') {
				var addWidgets = function(conf, disabled, _widgets) {
					array.forEach(conf, function(variable) {
						var type = TextBox;
						var value = variable.value;
						var additionalParams = {};
						if (variable.type === 'bool') {
							type = CheckBox;
							value = tools.isTrue(value);
						} else if (variable.type == 'list') {
							type = ComboBox;
							additionalParams.staticValues = [];
							array.forEach(variable.values, function(val, i) {
								var label = variable.labels[i] || val;
								additionalParams.staticValues.push({
									id: val,
									label: label
								});
							});
						}
						var widget = {
							name: variable.id,
							type: type,
							label: variable.description,
							disabled: disabled,
							value: value
						};
						widget = lang.mixin(widget, additionalParams);
						widgets.push(widget);
					});
				};
				addWidgets(array.filter(this.app.config, function(w) { return !w.advanced; }), false, widgets);
			}
			if (widgets.length) {
				this._configForm = new Form({
					widgets: widgets
				});
				var titlePane = new TitlePane({
					'class': 'umcAppConfigTitlePane',
					title: _('Configure %s', entities.encode(this.app.name))
				});
				titlePane.addChild(this._configForm);
				this._container.addChild(titlePane);
			}
		},

		showRequirements: function(label, stressedRequirements, appDetailsPage) {
			var opts = {
				appDetailsDialog: this,
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
					container.addChild(new Text({
						content: '<hr/>'
					}));
					container.addChild(new Text({
						content: foundRequirement.toHTML(this.app, details)
					}));
					if (foundRequirement.solution) {
						container.addChild(new Button({
							name: 'solution' + i,
							label: foundRequirement.buttonLabel(this.app, details),
							callback: lang.hitch(this, function() {
								opts.action = this.actionLabel;
								var deferred = foundRequirement.solution(opts, details);
								if (!foundRequirement.stayAfterSolution) {
									when(deferred).always(lang.hitch(this, 'onBack', false));
								}
							})
						}));
					}
				}));
				this._container.addChild(container);
			}
		},

		showHardRequirements: function(hardRequirements, appDetailsPage) {
			this.showRequirements(_('Continuation is not possible'), hardRequirements, appDetailsPage);
		},

		showSoftRequirements: function(softRequirements, appDetailsPage) {
			this.showRequirements(_('Continuation is not recommended'), softRequirements, appDetailsPage);
		},

		showUp: function() {
			this.onShowUp();
			return this._continueDeferred;
		},

		showErrataHint: function() {
			var repositoryButton = lang.replace('<a href="javascript:void(0)" onclick="require(\'umc/app\').openModule(\'appcenter\', \'components\')">{name}</a>', {name: _('Repository Settings')});
			this._container.addChild(new Text({
				content: _('These changes contain <strong>all package upgrades available</strong> and thus may <strong>include errata updates</strong>. If this is not intended, the corresponding components have to be temporarily deactivated first using the tab "%s" in the App Center.', repositoryButton),
				style: {paddingBottom: '.25em'}
			}));
		},

		showUnreachableHint: function(unreachable, masterUnreachable) {
			var componentID = this.app.candidateComponentID || this.app.componentID;
			var label = _('The server tried to connect to the involved systems.') + ' ' + _('The following hosts cannot be reached or do not have access to the App Center server:');
			this._container.addChild(new Text({
				content: label + '<ul><li>' + array.map(unreachable, function(v) { return entities.encode(v); }).join('</li><li>') + '</li></ul>'
			}));
			if (!masterUnreachable) {
				var cmdLine = lang.replace('univention-add-app {component_id} -m', {component_id: entities.encode(componentID)});
				var commandHint = '<strong>' + _('Attention!') + '</strong>' + ' ' + _('This application requires an extension of the LDAP schema.') + ' ' + _('Be sure to execute the following command as root on all of these backup servers <em>after</em> installing the application.') + '</td></tr><tr><td colspan="2"><pre>' + cmdLine + '</pre>';
				this._container.addChild(new Text({
					content: commandHint
				}));
			}
		},

		showPackageChanges: function(install, remove, broken, incompatible, opened, host) {
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
				this._container.addChild(new Text({
					content: '<p>' + _('The version of the remote App Center is <strong>incompatible</strong> with the local one. Please update your hosts.') + '</p>'
				}));
			}

			var changeLabels = [];
			_packageChangeLabel(install, _('1 package will be installed / upgraded'), _('{0} packages will be installed / upgraded'), changeLabels);
			_packageChangeLabel(remove, '<strong>' + _('1 package will be removed') + '</strong>', '<strong>' + _('{0} packages will be removed') + '</strong>', changeLabels);
			_packageChangeLabel(broken, '<strong>' + _('1 package is erroneous') + '</strong>', '<strong>' + _('{0} packages are erroneous') + '</strong>', changeLabels);
			if (!changeLabels.length) {
				changeLabels = '<p>' + _('No software changes on %s are necessary.', host || _('this host')) + '</p>';
			} else {
				changeLabels = '<p>' + _('The following software changes on %s will be applied: ', host || _('this host')) + changeLabels.join(', ') + '</p>';
			}
			this._container.addChild(new Text({
				content: changeLabels
			}));

			var txt = '';
			txt += _packageChangesList(install, _('The following packages will be installed or upgraded:'));
			txt += _packageChangesList(remove, _('The following packages will be removed:'));
			txt += _packageChangesList(broken, _('This operation causes problems in the following packages that cannot be resolved:'));
			if (txt === '') {
				txt = '<p>' + _('No software changes are necessary.') + '</p>';
			}
			this._container.addChild(new TitlePane({
				'class': 'umcAppMoreTitlePane',
				title: _('More information...'),
				open: false,
				content: txt
			}));
		},

		onBack: function(continued) {
			// make sure that the user does not want to continue
			//   (could be called by a requirement.solution(), not by the buttons)
			// if this is called by "Continue" button, it is resolved() anyway
			if (this._continueDeferred) {
				this._continueDeferred.reject();
			}
		}
	});
});

