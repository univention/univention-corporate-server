define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/string",
	"dojo/query",
	"dojo/Deferred",
	"dojo/on",
	"dojo/aspect",
	"dojox/html/entities",
	"dijit/Menu",
	"dijit/MenuItem",
	"dijit/ProgressBar",
	"dijit/Dialog",
	"dijit/form/_TextBoxMixin",
	"umc/tools",
	"umc/dialog",
	"umc/widgets/Module",
	"umc/widgets/Page",
	"umc/widgets/Form",
	"umc/widgets/Grid",
	"umc/widgets/SearchForm",
	"umc/widgets/Tree",
	"umc/widgets/Tooltip",
	"umc/widgets/Text",
	"umc/widgets/ContainerWidget",
	"umc/widgets/CheckBox",
	"umc/widgets/ComboBox",
	"umc/widgets/TextBox",
	"umc/widgets/Button",
	"umc/widgets/HiddenInput",
	"umc/widgets/PasswordBox",
	"umc/modules/uvmm/CloudConnectionWizard",
	"umc/i18n!umc/modules/uvmm"
], function(declare, lang, array, string, query, Deferred, on, aspect, entities, Menu, MenuItem, ProgressBar, Dialog, _TextBoxMixin,
	tools, dialog, Module, Page, Form, Grid, SearchForm, Tree, Tooltip, Text, ContainerWidget,
	CheckBox, ComboBox, TextBox, Button, HiddenInput, PasswordBox, CloudConnectionWizard, _) {
	return declare('umc.modules.uvmm.EC2', [CloudConnectionWizard], {
		postMixInProperties: function() {
			this.inherited(arguments);
			this.pages = [{
				name: 'credentials',
				headerText: _('Create a new cloud connection.'),
				helpText: _('Please enter the corresponding credentials for the cloud connection. <a href="https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSGettingStartedGuide/AWSCredentials.html" target=_blank>Use this link to get information about AWS credentials</a>'),
				layout: [
					'name',
					'region',
					'access_id',
					'password',
				],
				widgets: [{
					name: 'name',
					type: TextBox,
					label: _('Name'),
					required: true
				}, {
					name: 'access_id',
					type: TextBox,
					label: _('Access Key ID'),
					required: true
				}, {
					name: 'password',
					type: PasswordBox,
					label: _('Secret Access Key'),
					required: true
				}, {
					name: 'region',
					type: ComboBox,
					staticValues: [
						{ id: 'EC2_EU_WEST', label: 'EU (Ireland)' },
						{ id: 'EC2_US_EAST', label: 'US East (N. Virginia)' },
						{ id: 'EC2_US_WEST', label: 'US West (N. California)' },
						{ id: 'EC2_US_WEST_OREGON', label: 'US West (Oregon)' },
						{ id: 'EC2_AP_SOUTHEAST', label: 'Asia Pacific (Sydney)' },
						{ id: 'EC2_AP_NORTHEAST', label: 'Asia Pacific (Tokyo)' },
						{ id: 'EC2_AP_SOUTHEAST2', label: 'Asia Pacific (Singapore)' },
						{ id: 'EC2_SA_EAST', label: 'South America (São Paulo)' }
					],
					label: _('EC2 Region'),
					required: true
				}, {
					name: 'cloudtype',
					type: HiddenInput,
					value: this.cloudtype
				}]
			}];
		}
	});
});
