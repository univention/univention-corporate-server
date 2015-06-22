/*
 * Copyright 2013-2015 Univention GmbH
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
/*global define require console window */

define([
	"dojo/_base/lang",
	"dojo/_base/kernel",
	"dojo/_base/array",
	"dojo/request/xhr",
	"dojo/io-query",
	"dojo/query",
	"dojo/keys",
	"dojo/dom",
	"dojo/dom-construct",
	"dojo/dom-attr",
	"dojo/dom-style",
	"dojo/dom-class",
	"dojo/dom-geometry",
	"dojo/on",
	"dojo/router",
	"dojo/hash",
	"dijit/Menu",
	"dijit/MenuItem",
	"dijit/form/Button",
	"dijit/form/DropDownButton",
	"dijit/DropDownMenu",
	"dojox/form/Uploader",
	"put-selector/put",
	"./TextBox",
	"./text!/languages.json",
	"./text!/entries.json",
	"./text!/license",
	"./i18n!"
], function(lang, kernel, array, xhr, ioQuery, query, keys, dom, domConstruct, domAttr, domStyle, domClass, domGeometry, on, router, hash, Menu, MenuItem, Button, DropDownButton, DropDownMenu, Uploader, put, TextBox, _availableLocales, entries, license, _) {
	// strip starting/ending '"' and replace newlines
	license = license.substr(1, license.length - 2).replace(/\\n/g, '\n');

	// make sure that en-US exists
	var existsEnUsLocale = array.some(_availableLocales, function(ilocale) {
		return ilocale.id == 'en-US';
	});
	if (!existsEnUsLocale) {
		_availableLocales.push({
			id: 'en-US',
			label: 'English'
		});
	}

	var isTrue = function(input) {
		//('yes', 'true', '1', 'enable', 'enabled', 'on')
		if (typeof input == "string") {
			switch (input.toLowerCase()) {
				case 'yes':
				case 'true':
				case '1':
				case 'enable':
				case 'enabled':
				case 'on':
					return true;
			}
		}
		return false;
	};
	var hasLicense = Boolean(entries.license_uuid);
	var hasLicenseRequested = isTrue(entries.license_requested);
    var showRequestLicenseTab = !hasLicense && !hasLicenseRequested;


	return {
		_availableLocales: _availableLocales,
		_localeLang: kernel.locale.split('-')[0],
		_localeWithUnderscore: kernel.locale.replace('-', '_'),
		_resizeTimeout: null,
		_uploader: null,
		_tabIDs: [],

		registerRouter: function() {
			router.register(":tab", lang.hitch(this, function(data){
				this._removeError();
				this._focusTab(data.params.tab);
			}));
		},

		_focusTab: function(tabID){
			array.forEach(this._tabIDs, function(itabID) {
				var loadingNode = dom.byId(itabID + '-loading-bar');
				var tabNode = dom.byId(itabID + '-tab');
				var buttonNode = dom.byId(itabID + '-button');
				if (itabID == tabID) {
					put(loadingNode, '.focused');

					var animateTabTransition = function(){
						put(loadingNode, '!focused');
						put(tabNode, '!hide-tab');
						put(buttonNode, '.focused');
					};

					setTimeout(animateTabTransition, 600);
				} else {
					put(loadingNode, '!focused');
					put(tabNode, '.hide-tab');
					put(buttonNode, '!focused');
				}
			}, this);
		},

		_getAvailableLocales: function() {
			if ('availableLocales' in window) {
				return availableLocales;
			}
			return this._availableLocales;
		},

		_hasLanguagesDropDown: function() {
			return dom.byId('dropDownButton');
		},

		createLanguagesDropDown: function() {
			if (!this._hasLanguagesDropDown()) {
				return;
			}
			var _languagesMenu = new DropDownMenu({ style: "display: none;"});
			array.forEach(this._getAvailableLocales(), function(ilocale) {
				var newMenuItem = new MenuItem ({
					label: ilocale.label,
					id: ilocale.id,
					onClick: function() {
						if (ilocale.href) {
							// full href link is given... go to this URL
							window.location.href = ilocale.href;
							return;
						}

						// adjust query string parameter and reload page
						var queryObj = {};
						var queryString = window.location.search;
						if (queryString.length) {
							// cut off the '?' character
							queryObj = ioQuery.queryToObject(queryString.substring(1));
						}
						queryKey = ilocale.queryKey || 'lang';
						queryObj[queryKey] = ilocale.id;
						queryString = ioQuery.objectToQuery(queryObj);
						window.location.search = '?' + queryString;
					}
				});
				_languagesMenu.addChild(newMenuItem);
			});
			var _toggleButton = new DropDownButton({
				label: _("Language"),
				name: "languages",
				dropDown: _languagesMenu,
				id: "languagesDropDown"
			});
			domConstruct.place(_toggleButton.domNode, 'dropDownButton');
		},

		_createTitle: function() {
			var titleNode = dom.byId('title');
			put(titleNode, 'h1', _('Activation of Univention Corporate Server'));
			//put(titleNode, 'h2', _(''));
			put(titleNode, '!.dijitHidden');
		},

		_createNavButton: function(tabID) {
			var navNode = dom.byId('navigation');
			var buttonContainerNode = put(navNode, 'div.button-container');
			var buttonNode = put(buttonContainerNode, 'div.button#' + tabID + '-button');
			var loadingBarNode = put(buttonContainerNode, 'div.loading-bar#' + tabID + '-loading-bar');
			this._tabIDs.push(tabID);
		},

		_createRegistrationTab: function() {
			this._createNavButton('register');
			var contentNode = dom.byId('content');
			var tabNode = put(contentNode, 'div.tab#register-tab');
			put(tabNode, 'p > b', _('Request a license!'));
			put(tabNode, 'p', _('Please enter a valid e-mail address in order to activate the UCS system. The activation is required to use the App Center. In the next step you can upload the license file that has been sent to your email address.'));

			// create input field for email address
			this._email = new TextBox({
				inlineLabel: _('E-mail address'),
				regExp: '.+@.+',
				invalidMessage: _('No valid e-mail address.')
			});
			this._email.on("keyup", lang.hitch(this, function(evt){
				if(evt.keyCode === keys.ENTER){
					this._sendEmail();
				}
			}));
			put(tabNode, '>', this._email.domNode);
			this._email.startup();

			put(tabNode, 'p', {
				innerHTML: _('Details about the activation of a UCS license can be found in the <a href="http://docs.univention.de/manual.html#central:license" target="_blank">UCS manual</a>.')
			});

			// create input field for email address
			this._sendEmailButton = new Button({
				label: _('Send activation'),
				onClick: lang.hitch(this, function() {
					this._sendEmail();
				})
			});
			put(tabNode, '>', this._sendEmailButton.domNode);
			this._sendEmailButton.startup();
		},

		_sendEmail: function(){
			var data = {
				email: this._email.get('value'),
				licence: license
			};
			xhr.post('https://license.univention.de/keyid/conversion/submit', {
				data: data,
				handleAs: 'text',
				headers: {
					'X-Requested-With': null
				}
			}).then(function() {
				router.go('upload');
			}, lang.hitch(this, function(err) {
				var status_code = err.response.status;
				var error_details = null;
				if(status_code >= 400 && status_code <= 500){
					error_details = put('html');
					error_details.innerHTML = err.response.data;
					error_details = error_details.getElementsByTagName('span')[0].innerText;
				} else {
					error_details = _('An unknown error occured. Please try it again later!');
				}
				var error_msg = _('Error ') + status_code + ': ' + error_details;
				this._showError(error_msg);
				console.log(err);
			}));
		},

		_showError: function(error_msg){
			var currentTabNode = query(".tab:not(.hide-tab)")[0];
			var errorNode = dom.byId('error');
			if(!errorNode){
				errorNode = put('div[id=error]');
				put(currentTabNode, 'div', errorNode);
			}
			errorNode.innerHTML = error_msg;
		},

		_removeError: function(){
			var errorNode = dom.byId('error');
			if(errorNode){
				put(errorNode, "!");
			}
		},

		_createUploader: function() {
			// until Dojo2.0 "dojox.form.Uploader" must be used!
			this._uploader = new dojox.form.Uploader({
				url: '/license',
				name: 'license',
				label: _('Upload license file'),
				uploadOnSelect: true,
				getForm: function() {
					// make sure that the Uploader does not find any of our encapsulating forms
					return null;
				}
			});
			put(this._uploader.domNode, '.umcButton[display=inline-block]');
			//this._uploader.set('iconClass', 'umcIconAdd');
			this._uploader.on('complete', lang.hitch(this, function(evt) {
				console.log('### upload completet: ' + evt);
				if(evt.toLowerCase().indexOf('successful') > -1){
					router.go('finished');
				} else {
					//var error_msg = _('Error: Invalid license file. Please try again or request a new one.');
					this._showError(evt);
				}
			}));
			this._uploader.on('error', lang.hitch(this, function(evt){ 
				console.log('### upload error: ' + evt);
				//var error_msg = _('Error: Invalid license file. Please try again or request a new one.');
				this._showError(evt);
			}));
			return this._uploader.domNode;
		},

		_createUploadTab: function() {
			this._createNavButton('upload');
			var contentNode = dom.byId('content');
			var tabNode = put(contentNode, 'div.tab#upload-tab');
			var uploaderNode = this._createUploader();
			put(tabNode, 'p > b', _('You have got mail!'));
			put(tabNode, 'p', _('A license file should have been sent to your email address. Upload the license file from the email to activate your UCS instance.'));
			var backNode = put(tabNode, 'p');
			backNode.innerHTML = _('Note: If you did not received an email, please also check your spam directory or <a href="/#register">request a new one.</a>');
			put(tabNode, '>', uploaderNode);
			this._uploader.focus();
			this._uploader.startup();
		},

		_createFinishedTab: function() {
			this._createNavButton('finished');
			var contentNode = dom.byId('content');
			var tabNode = put(contentNode, 'div.tab#finished-tab');
			this._continueButton = new Button({
				label: _('Continue'),
				onClick: lang.hitch(this, function(){ 
					this._continue();
				})
			});
			put(tabNode, 'p > b', _('Activation successful!'));
			put(tabNode, 'p', _('The App Appliance is now activated. Click continue to visit the Univention Management Console (UMC).'));
			put(tabNode, '>', this._continueButton.domNode);
			this._continueButton.focus();
			this._continueButton.startup();
		},

		_continue: function(){
			location.href = "/umc" + location.search + "&username=Administrator";
		},

		createElements: function() {
			this._createTitle();
			this._createRegistrationTab();
			this._createUploadTab();
			this._createFinishedTab();
		},

		start: function() {
			this.registerRouter();
			this.createLanguagesDropDown();
			this.createElements();
			// check if license already requested
			console.log('### entries: ', entries);
			if(entries.license_requested === "true"){
				router.startup('upload');
			} else {
				router.startup('register');
			}
		}
	};
});

