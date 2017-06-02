/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojox/html/entities",
	"umc/tools",
	"umc/widgets/Form",
	"umc/widgets/Text",
	"umc/widgets/TextBox",
	"umc/widgets/Uploader",
	"umc/widgets/PasswordBox",
	"umc/widgets/CheckBox",
	"umc/widgets/ComboBox",
	"umc/widgets/ContainerWidget",
	"umc/widgets/TitlePane",
	"umc/modules/appcenter/AppSettingsFileUploader",
	"umc/i18n!umc/modules/appcenter"
], function(declare, lang, array, entities, tools, Form, Text, TextBox, Uploader, PasswordBox, CheckBox, ComboBox, ContainerWidget, TitlePane, AppSettingsFileUploader, _) {
	return {
		getWidgets: function(app, values, phase) {
			var ret = [];
			var staticValues;
			array.forEach(app.settings, function(variable) {
				if ((variable.write || []).indexOf(phase) === -1 && (variable.read || []).indexOf(phase) === -1) {
					return;
				}
				var value = values[variable.name] || null;
				var params = {
					name: variable.name,
					_groupName: variable.group,
					required: variable.required,
					label: variable.description,
					disabled: (variable.read || []).indexOf(phase) !== -1,
					value: value
				};
				if (variable.type == 'String') {
					ret.push(lang.mixin(params, {
						type: TextBox
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
						type: PasswordBox
					}));
				} else if (variable.type == 'File') {
					ret.push(lang.mixin(params, {
						type: AppSettingsFileUploader,
						content: ''
					}));
				} else if (variable.type == 'PasswordFile') {
					ret.push(lang.mixin(params, {
						type: PasswordBox
					}));
				} else if (variable.type == 'Status') {
					ret.push(lang.mixin(params, {
						type: Text,
						content: '<h2>' + params.name + '</h2>' + params.value,
						_groupName: variable.group
					}));
				}
			});
			return ret;
		},

		getForm: function(app, values, phase) {
			var widgets = this.getWidgets(app, values, phase);
			if (widgets.length === 0) {
				return;
			}
			var groups = this.getGroups(app, widgets);
			var layout = [];
			array.forEach(groups, function(group, i) {
				var groupName = '_group' + i;
				widgets.push({
					type: Text,
					name: groupName,
					content: '<h2>' + group.label + '</h2>'
				});
				layout.push(groupName);
				layout = layout.concat(array.map(group.widgets, function(w) { return w.name; }));
			});
			return new Form({
				widgets: widgets,
				layout: layout
			});
		},

		getGroups: function(app, widgets) {
			var groups = [];
			array.forEach(app.settings, function(setting) {
				if (! setting.group) {
					return;
				}
				var widget = array.filter(widgets, function(_widget) {
					return _widget._groupName !== setting.name;
				})[0];
				if (! widget) {
					return;
				}

				var groupDef = array.filter(groups, function(group) {
					return group.label == setting.group;
				})[0];
				if (! groupDef) {
					groupDef = {label: setting.group, widgets: []};
					groups.push(groupDef);
				}
				groupDef.widgets.push(widget);
			});
			if (! groups.length) {
				groups = [{label: _('Settings'), widgets: widgets.slice()}];
			}
			return groups;
		}
	};
});
