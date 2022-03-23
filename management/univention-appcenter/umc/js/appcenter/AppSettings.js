/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"umc/tools",
	"umc/widgets/Text",
	"umc/widgets/TextBox",
	"umc/widgets/NumberSpinner",
	"umc/widgets/PasswordInputBox",
	"umc/widgets/CheckBox",
	"umc/widgets/ComboBox",
	"./AppSettingsFileUploader",
	"./AppSettingsForm",
	"umc/i18n!umc/modules/appcenter"
], function(declare, lang, array, tools, Text, TextBox, NumberSpinner, PasswordInputBox, CheckBox, ComboBox, AppSettingsFileUploader, AppSettingsForm, _) {
	return {
		getWidgets: function(app, values, phase) {
			var ret = [];
			var staticValues;
			array.forEach(app.settings, function(variable) {
				if ((variable.show || []).indexOf(phase) === -1 && (variable.show_read_only || []).indexOf(phase) === -1) {
					return;
				}
				var required;
				if (variable.required == null) {
					required = false;
				} else {
					required = variable.required;
				}
				var value = values[variable.name] || null;
				var params = {
					name: variable.name,
					_groupName: variable.group || _('Settings'),
					required: required,
					label: variable.description,
					disabled: (variable.show_read_only || []).indexOf(phase) !== -1 || values[variable.name] === undefined,
					value: value
				};
				if (variable.type == 'String') {
					ret.push(lang.mixin(params, {
						type: TextBox
					}));
				} else if (variable.type == 'Int') {
					ret.push(lang.mixin(params, {
						type: NumberSpinner
					}));
				} else if (variable.type == 'Bool') {
					ret.push(lang.mixin(params, {
						type: CheckBox,
						value: tools.isTrue(params.value)
					}));
				} else if (variable.type == 'List') {
					staticValues = array.map(variable.values, function(val, i) {
						var label = variable.labels[i] || val;
						return {
							id: val,
							label: label
						};
					});
					ret.push(lang.mixin(params, {
						type: ComboBox,
						staticValues: staticValues
					}));
				} else if (variable.type == 'UDMList') {
					staticValues = array.map(variable.values, function(val, i) {
						var label = variable.labels[i] || val;
						return {
							id: val,
							label: label
						};
					});
					ret.push(lang.mixin(params, {
						type: ComboBox,
						staticValues: staticValues
					}));
				} else if (variable.type == 'Password') {
					ret.push(lang.mixin(params, {
						type: PasswordInputBox
					}));
				} else if (variable.type == 'File') {
					if (params.value) {
						params.data = {content: params.value};
					}
					ret.push(lang.mixin(params, {
						type: AppSettingsFileUploader,
						fileName: variable.filename
					}));
				} else if (variable.type == 'PasswordFile') {
					ret.push(lang.mixin(params, {
						type: PasswordInputBox
					}));
				} else if (variable.type == 'Status') {
					if (value) {
						ret.push(lang.mixin(params, {
							type: Text,
							content: value,
							_groupName: params._groupName
						}));
					}
				}
			});
			return ret;
		},

		getGroups: function(app, widgets) {
			var groups = [];
			array.forEach(app.settings, function(setting) {
				var groupName = setting.group || _('Settings');
				if (groups.indexOf(groupName) === -1) {
					groups.push(groupName);
				}
			});
			groups = array.map(groups, function(group) {
				var _widgets = array.filter(widgets, function(widget) {
					return group === widget._groupName;
				});
				var groupDef = {label: group, widgets: _widgets};
				return groupDef;
			});
			return groups;
		},

		getFormConf: function(app, values, phase, smallHeaders) {
			var widgets = this.getWidgets(app, values, phase);
			if (widgets.length === 0) {
				return null;
			}
			var groups = this.getGroups(app, widgets);
			var layout = [];
			array.forEach(groups, function(group, i) {
				if (group.widgets.length === 0) {
					return null;
				}
				var groupName = '_group' + i;
				var content = '<h2>' + group.label + '</h2>';
				if (smallHeaders) {
					content = '<h3>' + group.label + '</h2>';
				}
				widgets.push({
					type: Text,
					name: groupName,
					content: content
				});
				layout.push(groupName);
				layout = layout.concat(array.map(group.widgets, function(w) { return w.name; }));
			});
			return {
				widgets: widgets,
				layout: layout
			};
		},

		getForm: function(app, values, phase, smallHeaders) {
			var formConf = this.getFormConf(app, values, phase, smallHeaders);
			return formConf ? new AppSettingsForm(formConf) : null;
		},

		getFormConfDeferred: function(app, phase, smallHeaders) {
			return tools.umcpCommand('appcenter/config', {app: app.id, phase: phase}).then(lang.hitch(this, function(data) {
				return this.getFormConf(app, data.result.values, phase, smallHeaders);
			}));
		},

		getFormDeferred: function(app, phase, smallHeaders) {
			return this.getFormConfDeferred(app, phase, smallHeaders).then(function(formConf) {
				return formConf ? new AppSettingsForm(formConf) : null;
			});
		}
	};
});
