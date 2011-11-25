/*
 * Copyright 2011 Univention GmbH
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
/*global dojo dijit dojox umc console */

dojo.provide("umc.widgets.Uploader");

dojo.require("dojox.form.Uploader");
dojo.require("dojox.form.uploader.plugins.IFrame");
dojo.require("umc.widgets.ContainerWidget");
dojo.require("umc.widgets.Button");
dojo.require("umc.widgets._FormWidgetMixin");
dojo.require("umc.i18n");
dojo.require("umc.tools");
dojo.require("umc.dialog");

dojo.declare("umc.widgets.Uploader", [ umc.widgets.ContainerWidget, umc.widgets._FormWidgetMixin, umc.i18n.Mixin ], {
	'class': 'umcUploader',

	i18nClass: 'umc.app',

	// command: String
	//		The UMCP command to which the data shall be uploaded.
	//		If not given, the data is sent to umcp/upload which will return the
	//		file content encoded as base64.
	command: '',

	// buttonLabel: String
	//		The label that is displayed on the upload button.
	buttonLabel: 'Upload',

	// showClearButton: Boolean
	//		The clear button is shown only if this attribute is set to true.
	showClearButton: true,

	// clearButtonLabel: String
	//		The label that is displayed on the upload button.
	clearButtonLabel: 'Clear data',

	// data: Object
	//		An object containing the file data that has been uploaded.
	data: null,

	// value: String
	//		The content of the base64 encoded file data.
	value: "",

	// maxSize: Number
	//		A size limit for the uploaded file.
	maxSize: 524288,

	// make sure that no sizeClass is being set
	sizeClass: null,

	// this form element should always be valid
	valid: true,

	// reference to the dojox.form.Uploader instance
	_uploader: null,

	// internal reference to 'clear' button
	_clearButton: null,

	// internal reference to the original user specified label
	_origButtonLabel: null,

	// internal flag that indicates that the data is being set
	_settingData: false,

	constructor: function() {
		this.buttonLabel = this._('Upload');
		this.clearButtonLabel = this._('Clear data');
	},

	postMixInProperties: function() {
		this.inherited(arguments);

		// save the original label
		this._origButtonLabel = this.buttonLabel;
	},

	buildRendering: function() {
		this.inherited(arguments);
		
		this._uploader = new dojox.form.Uploader({
			url: '/umcp/upload' + (this.command ? '/' + this.command : ''),
			label: this.buttonLabel,
			getForm: function() {
				// make sure that the Uploader does not find any of our encapsulating forms
				return null;
			}
		});
		dojo.addClass(this._uploader.button.domNode, 'umcButton');
		this._uploader.button.set('iconClass', 'umcIconAdd');
		dojo.style(this._uploader.button.domNode, 'display', 'inline-block');
		this.addChild(this._uploader);

		if ( this.showClearButton ) {
			this._clearButton = new umc.widgets.Button({
				label: this.clearButtonLabel,
				iconClass: 'umcIconDelete',
				callback: dojo.hitch(this, function() {
					this.set('data', null);
				})
			});
			this.addChild(this._clearButton);
		}
	},
	
	postCreate: function() {
		this.inherited(arguments);

		// as soon as the user has selected a file, start the upload
		this.connect(this._uploader, 'onChange', function(data) {
			var allOk = true;
			dojo.forEach(data, function(ifile) {
				allOk = allOk && ifile.size <= this.maxSize;
				return allOk;
			}, this);
			if (!allOk) {
				umc.dialog.alert(this._('File cannot be uploaded, its maximum size may be %.1f MB.', this.maxSize / 1048576.0));
			}
			else {
				this._updateLabel();
				this._uploader.upload({
					iframe: (this._uploader.uploadType === 'iframe') ? true : false
				});
			}
		});

		// hook for showing the progress
		/*this.connect(this._uploader, 'onProgress', function(data) {
			console.log('onProgress:', dojo.toJson(data));
			this._updateLabel(data.percent);
		});*/

		// notification as soon as the file has been uploaded
		this.connect(this._uploader, 'onComplete', function(data) {
			this.set('data', data.result[0]);
			this.onUploaded(this.data);
			this._resetLabel();
		});

		// setup events
		this.connect(this._uploader, 'onCancel', '_resetLabel');
		this.connect(this._uploader, 'onAbort', '_resetLabel');
		this.connect(this._uploader, 'onError', '_resetLabel');

		// update the view
		this.set('value', this.value);
	},

	_setDataAttr: function(newVal) {
		this.data = newVal;
		this._settingData = true;
		this.set( 'value', newVal && 'content' in newVal ? newVal.content : '' );
		this._settingData = false;
	},

	_setValueAttr: function(newVal) {
		if (!this._settingData) {
			this.data = null;
		}
		this.value = newVal;

		if ( this.showClearButton ) {
			// decide whether to show/hide remove button
			dojo.toggleClass(this._clearButton.domNode, 'dijitHidden', !(dojo.isString(this.value) && this.value !== ""));
		}

		// send events
		this.onChange(newVal);
		this.updateView(this.value, this.data);
	},

	_resetLabel: function() {
		this.set('disabled', false);
		this.set('buttonLabel', this._origButtonLabel);
		this._uploader.reset();
	},

	_updateLabel: function() {
		if (!this.get('disabled')) {
			// make sure the button is disabled
			this.set('disabled', true);
		}
		this.set('buttonLabel', this._('Uploading...'));
	},

	_setButtonLabelAttr: function(newVal) {
		this.buttonLabel = newVal;
		this._uploader.button.set('label', newVal);
	},

	_setDisabledAttr: function(newVal) {
		this._uploader.set('disabled', newVal);
		dojo.style(this._uploader.button.domNode, 'display', 'inline-block');
	},

	_getDisabledAttr: function() {
		return this._uploader.get('disabled');
	},

	onUploaded: function(data) {
		// event stub
	},

	onChange: function(data) {
		// event stub
	},

	updateView: function(value, data) {
		// summary:
		//		Custom view function that renders the file content that has been uploaded.
		//		The default is empty.
	}
});



