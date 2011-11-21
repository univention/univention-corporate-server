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
/*global dojo dijit dojox umc console window */

dojo.provide("umc.widgets.LoginDialog");

dojo.require("dojox.widget.Dialog");
dojo.require("umc.i18n");
dojo.require("umc.tools");
dojo.require("umc.widgets.ContainerWidget");
dojo.require("umc.widgets.Form");
dojo.require("umc.widgets.StandbyMixin");
dojo.require("umc.widgets.Text");

dojo.declare('umc.widgets.LoginDialog', [ dojox.widget.Dialog, umc.widgets.StandbyMixin, umc.i18n.Mixin ], {
	// our own variables
	_container: null,
	_passwordTextBox: null,
	_usernameTextBox: null,
	_text: null,
	_form: null,
	_container: null,

	'class': 'umcLoginDialog',

	// use the framework wide translation file
	i18nClass: 'umc.app',

	availableLanguages: null,

	postMixInProperties: function() {
		dojo.mixin(this, {
			closable: false,
			modal: true,
			sizeDuration: 900,
			sizeMethod: 'chain',
			sizeToViewport: false,
			dimensions: [300, 270]
		});

		dojo.mixin(this, {
			availableLanguages: [
				{ id: 'de-DE', label: this._('German') },
				{ id: 'en-US', label: this._('English') }
			] } );
	},

	defaultLang: function () {
		// dojo.locale is set in the index.html either via the query string in the URL,
		// via a cookie, or via dojo automatically
		var lowercase_locale = dojo.locale.toLowerCase();
		var exact_match = dojo.filter( this.availableLanguages, function( item ) { return lowercase_locale == item.id.toLowerCase(); } );
		if ( exact_match.length > 0 ) {
			return exact_match[ 0 ].id;
		}

		// fallbacks
		var default_language = null;

		// if dojo.locale is 'de' or 'de-XX' choose the first locale that starts with 'de'
		var short_locale = lowercase_locale.slice( 0, 2 );
		dojo.forEach( this.availableLanguages, function( lang ) {
			if ( lang.id.toLowerCase().indexOf(short_locale ) === 0 ) {
				default_language = lang.id;
				return false;
			}
		}, this );

		if ( null === default_language ) {
			default_language = 'en-US';
		}

		console.log( 'new locale ' + default_language );

		return default_language;
	},

	buildRendering: function() {
		this.inherited(arguments);

		// adjust CSS classes for the title
		dojo.addClass(this.titleNode, 'umcLoginDialogTitle');
		dojo.addClass(this.titleBar, 'umcLoginDialogTitleBar');

		var default_lang = this.defaultLang();

		var widgets = [{
			type: 'TextBox',
			name: 'username',
			value: dojo.cookie('UMCUsername') || '',
			//description: this._('The username of your domain account.'),
			label: this._('Username'),
			sizeClass: null
		}, {
			type: 'PasswordBox',
			name: 'password',
			//description: this._('The password of your domain account.'),
			label: this._('Password'),
			sizeClass: null
		}, {
			type: 'ComboBox',
			name: 'language',
			staticValues: this.availableLanguages,
			value: default_lang,
			//description: this._('The language for the login session.'),
			label: this._('Language'),
			sizeClass: null
		}];

		var buttons = [{
			name: 'submit',
			label: this._('Login'),
			callback: dojo.hitch(this, function(values) {
				// call LoginDialog.onSubmit() and clear password
				this._authenticate(values.username, values.password);
				this._form.elementValue('password', '');
			})
		} ];

		var layout = [['username'], ['password'], ['language']];

		this._form = new umc.widgets.Form({
			//style: 'width: 100%',
			widgets: widgets,
			buttons: buttons,
			layout: layout,
			style: 'margin-left: auto; margin-right: auto; width: 180px;'
		}).placeAt(this.containerNode);
		this._form.startup();

		// register onChange event
		this.connect(this._form._widgets.language, 'onChange', function(lang) {
			if (lang != dojo.locale) {
				// disable the entry fields
				this._form.getWidget('username').set('disabled', true);
				this._form.getWidget('password').set('disabled', true);

				// reload the page when a different language is selected
				var query = dojo.queryToObject(window.location.search.substring(1));
				query.lang = lang;
				dojo.cookie('UMCLang', query.lang, { expires: 100, path: '/' });
				window.location.search = '?' + dojo.objectToQuery(query);
			}
		});

		// put the layout together
		this._container = new umc.widgets.ContainerWidget({});
		this._text = new umc.widgets.Text({
			style: 'margin-left: auto; margin-right: auto; margin-top: 1em; width: 250px;',
			content: ''
		});
		this._container.addChild(this._text);
		this._container.addChild(this._form);
		this.set('content', this._container);
	},

	postCreate: function() {
		// call superclass' postCreate()
		this.inherited(arguments);

		// hide the close button
		dojo.style(this.closeButtonNode, 'display', 'none');
	},

	_showContent: function() {
		this.inherited(arguments);

		// focus on password input field if username is already given by cookie
		if (this._form.elementValue('username')) {
			this._form._widgets.password.focus();
		}

		// update text and disable/enable username input field
		var msg = '';
		if (umc.tools.status('setupGui')) {
			// user has already logged in before, show message for relogin
			msg = this._('Your session has been closed due to inactivity. Please login again.');
			// disable username field
			this._form.getWidget('username').set('disabled', true);
		}
		else {
			msg = this._('Welcome to Univention Management Console. Please enter your domain username and password for login.');
			this._form.getWidget('username').set('disabled', false);
		}
		this._text.set('content', '<p>' + msg + '</p>');
	},

	_onKey:  function(evt) {
		// ignore ESC key
		if (evt.charOrCode == dojo.keys.ESCAPE) {
			return;
		}

		// otherwise call the standard handler
		this.inherited(arguments);
	},

	_authenticate: function(username, password) {
		this.standby(true);
		umc.tools.umcpCommand('auth', {
			username: username,
			password: password
		}).then(dojo.hitch(this, function(data) {
			// disable standby in any case
			this.standby(false);

			// make sure that we got data
			this.onLogin(username);
			this.hide();
		}), dojo.hitch(this, function(error) {
			// disable standby in any case
			this.standby(false);
		}));
	},

	onLogin: function(/*String*/ username) {
		// event stub
	}
});


