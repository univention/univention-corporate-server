/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"umc/widgets/ComboBox",
	"umc/widgets/TextBox",
	"umc/widgets/HiddenInput",
	"umc/widgets/PasswordBox",
	"umc/modules/uvmm/CloudConnectionWizard",
	"umc/i18n!umc/modules/uvmm"
], function(declare, lang, ComboBox, TextBox, HiddenInput, PasswordBox, CloudConnectionWizard, _) {
	var _invalidUrlMessage = _('The url is invalid!<br/>Expected format is: <i>http(s)://</i>');
	var _validateUrl = function(url) {
		url = url || '';
		var _regUrl = /^(http|https)+:\/\//;
		var isUrl = _regUrl.test(url);
		var acceptEmtpy = !url && !this.required;
		return acceptEmtpy || isUrl;
	};

	return declare('umc.modules.uvmm.OpenStack', [CloudConnectionWizard], {
		postMixInProperties: function() {
			this.inherited(arguments);
			this.pages = [{
				name: 'credentials',
				headerText: _('Create a new cloud connection.'),
				helpText: _('Please enter the corresponding credentials for the cloud connection:'),
				layout: [
					'name',
					'username',
					'auth_version',
					[ 'password', 'auth_token' ],
					'auth_url',
					'search_pattern',
					'tenant',
					'service_region',
					'service_type',
					'service_name',
					'base_url'
				],
				widgets: [{
					name: 'cloudtype',
					type: HiddenInput,
					value: this.cloudtype
				}, {
					name: 'name',
					type: TextBox,
					label: _('Name'),
					required: true
				}, {
					name: 'username',
					type: TextBox,
					label: _('Username'),
					required: true
				}, {
					name: 'auth_version',
					type: ComboBox,
					label: _('Use the following authentication type'),
					staticValues: [
						{ id: '2.0_password', label: _('Password') },
						{ id: '2.0_apikey', label: _('API Key') }
					],
					onChange: lang.hitch(this, function(value){
						var password = this.getWidget('password');
						password.set('visible', value.indexOf('2.0_apikey') < 0);
						password.set('value', '');
						var auth_token = this.getWidget('auth_token');
						auth_token.set('visible', value.indexOf('2.0_password') < 0);
						auth_token.set('value', '');
					}),
					required: true
				}, {
					name: 'password',
					type: PasswordBox,
					label: _('Password'),
					depends: 'auth_version',
					labelConf: {'style': 'padding-right: 0px;'},
					required: true
				}, {
					name: 'auth_token',
					type: PasswordBox,
					label: _('API Key'),
					depends: 'auth_version',
					labelConf: {'style': 'padding-right: 0px;'},
					required: true
				}, {
					name: 'auth_url',
					type: TextBox,
					label: _('Authentication URL endpoint'),
					required: true,
					validator: _validateUrl,
					invalidMessage: _invalidUrlMessage
				}, {
					name: 'tenant',
					type: TextBox,
					label: _('Tenant'),
					required: false
				}, {
					name: 'service_region',
					type: TextBox,
					label: _('Service region'),
					required: false
				}, {
					name: 'service_type',
					type: TextBox,
					label: _('Service type'),
					value: 'compute',
					required: false
				}, {
					name: 'service_name',
					type: TextBox,
					label: _('Service name'),
					value: 'nova',
					required: false
				}, {
					name: 'search_pattern',
					type: TextBox,
					value: '*',
					label: _('Search pattern for images'),
					required: true,
					description: _('When creating new cloud instances with this connection, only images that match the pattern are available. "*" finds all images.')
				}, {
					name: 'base_url',
					type: TextBox,
					label: _('Service URL endpoint'),
					required: false,
					validator: _validateUrl,
					invalidMessage: _invalidUrlMessage
				}]
			}];
		}
	});
});
