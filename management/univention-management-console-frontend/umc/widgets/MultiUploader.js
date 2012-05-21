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

dojo.provide("umc.widgets.MultiUploader");

dojo.require("umc.widgets.ContainerWidget");
dojo.require("umc.i18n");
dojo.require("umc.widgets.Button");
dojo.require("umc.widgets.Uploader");
dojo.require("umc.widgets.MultiSelect");
dojo.require("umc.widgets.ProgressInfo");
dojo.require("umc.tools");
dojo.require("umc.dialog");

dojo.declare("umc.widgets.MultiUploader", [ umc.widgets.ContainerWidget, umc.widgets._FormWidgetMixin, umc.i18n.Mixin ], {
	'class': 'umcMultiUploader',

	i18nClass: 'umc.app',

	// command: String
	//		The UMCP command to which the data shall be uploaded.
	//		If not given, the data is sent to umcp/upload which will return the
	//		file content encoded as base64.
	command: '',

	// buttonLabel: String
	//		The label that is displayed on the upload button.
	buttonLabel: 'Upload',

	// value: String[]
	//		'value' contains an array of the uploaded file names.
	value: [],

	// maxSize: Number
	//		A size limit for the uploaded file.
	maxSize: 524288,

	// make sure that no sizeClass is being set
	sizeClass: null,

	// this form element should always be valid
	valid: true,

	/*=====
	// state: String
	//		Specifies in which state the widget is:
	//		'Complete' -> default,
	//		'Incomplete' -> uploads are not completed yet
	state: 'Complete',
	=====*/

	// internal reference to the MultiSelect widget containing all filenames
	_files: null,

	// internal reference to the current Uploader widget
	_uploader: null,

	// internal reference to the progress bar
	_progressBar: null,

	// button for removing entries
	_removeButton: null,

	// container for the upload and remove buttons
	_container: null,

	// internal reference to the currently uploading files
	_uploadingFiles: [],

	constructor: function() {
		this.buttonLabel = this._('Upload');
		this._uploadingFiles = [];
	},

	buildRendering: function() {
		this.inherited(arguments);

		// MultiSelect widget for displaying the file list
		this._files = new umc.widgets.MultiSelect({
			style: 'width: 50em'
		});
		this.addChild(this._files);

		this._createProgressBar();

		// prepare remove button and container for upload/remove buttons
		this._container = new umc.widgets.ContainerWidget({});
		this._container.addChild(new umc.widgets.Button({
			label: this._('Remove'),
			iconClass: 'umcIconDelete',
			onClick: dojo.hitch(this, '_removeFiles'),
			style: 'float: right;'
		}));
		this.addChild(this._container);

		// add the uploader button
		this._addUploader();
	},

	destroy: function() {
		this.inherited(arguments);

		if (this._progressBar) {
			// destroy the old progress bar
			this._progressBar.destroyRecursive();
		}
	},

	_getStateAttr: function() {
		return this._uploadingFiles.length ? 'Incomplete' : 'Complete';
	},

	_setValueAttr: function(newVal) {
		this._files.set('staticValues', newVal);
	},

	_getValueAttr: function() {
		return this._files.get('staticValues');
	},

	_setButtonLabelAttr: function(newVal) {
		this.buttonLabel = newVal;
		this._uploader.set('buttonLabel', newVal);
	},

	_setDisabledAttr: function(newVal) {
		this._files.set('disabled', newVal);
		this._uploader.set('disabled', newVal);
	},

	_getDisabledAttr: function() {
		return this._files.get('disabled');
	},

	_removeFiles: function() {
		var selectedFiles = this._files.get('value');
		if (!selectedFiles.length) {
			return;
		}

		// make sure we may remove the selected items
		dojo.when(this.canRemove(selectedFiles), dojo.hitch(this, function(doUpload) {
			if (!doUpload) {
				// removal canceled
				return;
			}

			// remove items
			var files = this.get('value');
			files = dojo.filter(files, function(ifile) {
				return dojo.indexOf(selectedFiles, ifile) < 0;
			});
			this.set('value', files);
		}));
	},

	_createProgressBar: function() {
		if (this._progressBar) {
			// destroy the old progress bar
			this._progressBar.destroyRecursive();
		}

		// create progress bar for displaying the upload information
		this._progressBar = new umc.widgets.ProgressInfo({
			maximum: 1
		});
		this._progressBar._progressBar.set('style', 'min-width: 30em;');
		this._progressBar.updateTitle(this._('No upload in progress'));
	},

	_updateProgress: function() {
		if (!this._progressBar) {
			return;
		}

		var currentVal = 0;
		var nDone = 0;
		dojo.forEach(this._uploadingFiles, function(ifile) {
			nDone += ifile.done || 0;
			currentVal += ifile.done ? 1.0 : ifile.decimal || 0;
		});
		currentVal = Math.min(currentVal / this._uploadingFiles.length, 0.99);
		if (!this._uploadingFiles.length || nDone == this._uploadingFiles.length) {
			// all uploads are finished
			this._progressBar.update(1, '', this._('Uploads finished'));
		}
		else {
			this._progressBar.update(currentVal, '', this._('Uploading... %d of %d files remaining.', this._uploadingFiles.length - nDone, this._uploadingFiles.length));
		}
	},

	_addUploader: function() {
		// create a new Uploader widget
		this._uploader = new umc.widgets.Uploader({
			showClearButton: false,
			buttonLabel: this.buttonLabel,
			command: this.command,
			maxSize: this.maxSize,
			canUpload: this.canUpload,
			style: 'float: left;'
		});
		this._container.addChild(this._uploader);

		// register events
		var uploader = this._uploader;
		var startedSignal = this.connect(uploader, 'onUploadStarted', function(file) {
			//console.log('### onUploadStarted:', dojo.toJson(file));
			this.disconnect(startedSignal);

			// add current file to the list of uploading items
			if (!this._uploadingFiles.length) {
				// first file being uploaded -> show the standby animation
				//this._createProgressBar();
				this._files.standby(true, this._progressBar);
			}
			this._uploadingFiles.push(file);
			this._updateProgress();

			var progressSignal = this.connect(uploader, 'onProgress', function(info) {
				// update progress information
				//console.log('### onProgress:', dojo.toJson(info));
				dojo.mixin(file, info);
				this._updateProgress();
			});
			var uploadSignal = this.connect(uploader, 'onUploaded', function() {
				// disconnect events
				//console.log('### onUploaded');
				this.disconnect(progressSignal);
				this.disconnect(uploadSignal);

				// update progress information
				file.done = true;
				this._updateProgress();

				// remove Uploader widget from container
				this.removeChild(uploader);
				uploader.destroyRecursive();

				// when all files are uploaded, update the internal list of files
				var allDone = true;
				dojo.forEach(this._uploadingFiles, function(ifile) {
					allDone = allDone && ifile.done;
				});
				if (allDone) {
					// add files to internal list of files
					this._files.standby(false);
					var vals = this.get('value');
					dojo.forEach(this._uploadingFiles, function(ifile) {
						//console.log('### adding:', ifile.name);
						vals.unshift(ifile.name);
					});
					this.set('value', vals);

					// clear the list of uploading files
					this._uploadingFiles = [];
				}
			});

			// hide uploader widget and add a new one
			dojo.style(uploader.domNode, {
				width: '0',
				overflow: 'hidden'
			});
			this._addUploader();
		});
	},

	canUpload: function(fileInfo) {
		// summary:
		//		Before uploading a file, this function is called to make sure
		//		that the given filename is valid. Return boolean or dojo.Deferred.
		// fileInfo: Object
		//		Info object for the requested file, contains properties 'name',
		//		'size', 'type'.
		return true;
	},

	canRemove: function(filenames) {
		// summary:
		//		Before removing a files from the current list, this function
		//		is called to make sure that the given file may be removed.
		//		Return boolean or dojo.Deferred.
		// filenames: String[]
		//		List of filenames.
		return true;
	},

	onUploaded: function(data) {
		// event stub
	},

	onChange: function(data) {
		// event stub
	}
});



