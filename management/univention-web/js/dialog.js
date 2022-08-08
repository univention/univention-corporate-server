/*
 * Like what you see? Join us!
 * https://www.univention.com/about-us/careers/vacancies/
 *
 * Copyright 2011-2022 Univention GmbH
 *
 * https://www.univention.de/
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
 * <https://www.gnu.org/licenses/>.
 */
/*global define,require,setTimeout */

define([
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/parser",
	"dojo/on",
	"dojo/topic",
	"dojo/Deferred",
	"dojo/dom-class",
	"dojo/dom-style",
	"umc/dialog/NotificationSnackbar",
	"umc/widgets/ConfirmDialog",
	"umc/widgets/Text",
	"umc/widgets/Form",
	"umc/widgets/NotificationsButton",
	"umc/tools",
	"umc/i18n/tools",
	"umc/i18n!"
], function(lang, array, parser, on, topic, Deferred, domClass, domStyle, NotificationSnackbar, ConfirmDialog, Text,
		Form, NotificationsButton, tools, i18nTools, _) {
	var dialog = {};
	lang.mixin(dialog, {

		contextNotify: function(/*innerHTML*/ message, options) {
			// summary:
			//		Show a snackbar notification on the bottom of the screen.
			//		(Snackbar notification from Google Material Design)
			// message:
			// 		The message that is shown in the snackbar notification
			// action:
			// 		A optional function that is executed when the action button
			// 		in the snackbar notification is pressed.
			// 		(The action button is only visible when an action is specified)
			// actionLabel:
			// 		The label that is shown in the action button.
			// 		(Only needed is action is specified)
			NotificationSnackbar.getInstance().then(function(snackbar) {
				snackbar.notify(message, options);
			});
		},

		contextWarn: function(/*innerHTML*/ message, options) {
			// summary:
			//		Show a snackbar warning notification on the bottom of the screen.
			//		(Snackbar notification from Google Material Design)
			// message:
			// 		The message that is shown in the snackbar notification
			// action:
			// 		A optional function that is executed when the action button
			// 		in the snackbar notification is pressed.
			// 		(The action button is only visible when an action is specified)
			// actionLabel:
			// 		The label that is shown in the action button.
			// 		(Only needed is action is specified)
			NotificationSnackbar.getInstance().then(function(snackbar) {
				snackbar.warn(message, options);
			});
		},

		notify: function(/*String*/ message, /*String?*/ component, /*Boolean?*/ truncate) {
			// summary:
			//		Add a notification to the notifications drop down menu.
			// message:
			//		The message that is displayed in the notification.
			// component:
			// 		The title for the notification.

			var item = {
				title: component || _('Notification'),
				content: message || ''
			};
			NotificationsButton.addNotification(item);
		},

		warn: function(/*String*/ message, /*String?*/ component, /*Boolean?*/ truncate) {
			// summary:
			//		Add a warning notification to the notifications drop down menu.
			// message:
			//		The message that is displayed in the notification.
			// component:
			// 		The title for the notification.

			var item = {
				title: component || _('Warning'),
				content: message || ''
			};
			NotificationsButton.addWarning(item);
		},

		_alertDialog: null, // internal reference for the alert dialog
		_alertDialogDeferred: null,

		alert: function(/*String*/ message, /* String? */ title, /* String? */ buttonLabel) {
			// summary:
			//		Popup an alert dialog with the given message string. The users needs to
			//		confirm the dialog by clicking on the 'OK' button.
			// message:
			//		The message that is displayed in the dialog.
			// title:
			//		An optional title for the popup window
			// buttonLabel:
			//		An alternative label for the button
			//
			if (this._alertDialogDeferred && !this._alertDialogDeferred.isFulfilled()) {
				this._alertDialogDeferred.reject();
			}
			this._alertDialogDeferred = new Deferred();

			// unhandled rejects (this._alertDialogDeferred.reject)
			// throw an error so we just respond to errors once with an empty callback
			this._alertDialogDeferred.then(function() {}, function() {});

			// create alert dialog the first time
			if (!this._alertDialog) {
				this._alertDialog = new ConfirmDialog({
					title: title || _('Notification'),
					closable: true,
					options: [{
						label: buttonLabel || _('Ok'),
						callback: lang.hitch(this, function() {
							// hide dialog upon confirmation by click on 'OK'
							this._alertDialogDeferred.resolve();
							this._alertDialog.hide();
						}),
						'default': true
					}]
				});

				// destroy the dialog when it is being closed
				this._alertDialog.on('hide', lang.hitch(this, function() {
					setTimeout(lang.hitch(this, function() {
						this._alertDialog.destroyRecursive();
						this._alertDialog = null;
						this._alertDialogDeferred.reject();
					}), 0);
				}));
			}

			// show the confirmation dialog
			this._alertDialog.set('message', message);
			// update title
			this._alertDialog.set('title', title || _('Notification'));
			//this._alertDialog.startup();
			this._alertDialog.show();
			return this._alertDialogDeferred;
		},

		confirm: function(/*String|_WidgetBase*/ message, /*Object[]*/ options, /*String?*/ title) {
			// summary:
			//		Popup a confirmation dialog with a given message string and a
			//		list of options to choose from.
			// description:
			//		This function provides a shortcut for ConfirmDialog.
			//		The user needs to confirm the dialog by clicking on one of
			//		multiple defined buttons (=choice). When any of the buttons
			//		is pressed, the dialog is automatically closed.
			//		The function returns a Deferred object. Registered callback
			//		methods are called with the corresponding choice name as parameter.
			// message:
			//		The message that is displayed in the dialog, can also be a _WidgetBase.
			// options:
			//		Array of objects describing the possible choices. Array is passed to
			//		ConfirmDialog as 'options' parameter. The property 'label' needs
			//		to be specified. The properties 'callback', 'name', 'auto', and 'default' are
			//		optional.
			//		The property 'default' renders the button for the default choice in the style
			//		of a submit button.
			//		If one single (!) item is specified with the property 'auto=true' and
			//		confirmations are switched off in the user preferences, the dialog is not shown
			//		and the callback function for this default option is executed directly.
			// title:
			//		Optional title for the dialog.
			//
			// example:
			//		A simple example that uses the 'default' property.
			// |	dialog.confirm(msg, [{
			// |	    label: Delete',
			// |	    callback: function() {
			// |			// do something...
			// |		}
			// |	}, {
			// |	    label: 'Cancel',
			// |	    'default': true
			// |	}]);
			// example:
			//		We may also refer the callback to a method of an object, i.e.:
			// |	var myObj = {
			// |		foo: function(answer) {
			// |			if ('delete' == answer) {
			// |				console.log('Item will be deleted!');
			// |			}
			// |		}
			// |	};
			// |	dialog.confirm('Do you want to delete the item?', [{
			// |	    label: 'Delete item',
			// |		name: 'delete',
			// |	    'default': true,
			// |	    callback: lang.hitch(myObj, 'foo')
			// |	}, {
			// |	    label: 'Cancel',
			// |		name: 'cancel',
			// |	    callback: lang.hitch(myObj, 'foo')
			// |	}]);

			// if the user has switched off confirmations, try to find a default option
			if (tools.preferences('confirm') === false) {
				var cb;
				var response;
				array.forEach(options, function(i, idx) {
					// check for default option
					if (true === i.auto) {
						cb = i.callback;
						response = i.name || idx;
						return false; // break loop
					}
				});
				if (cb && typeof cb == "function") {
					// we found a default item .. call the callback and exit
					cb(response);
					return;
				}
			}

			// create confirmation dialog
			var confirmDialog = new ConfirmDialog({
				title: title || _('Confirmation'),
				message: message,
				options: options,
				destroyOnCancel: true
			});

			// connect to 'confirm' event to close the dialog in any case
			var deferred = new Deferred();
			confirmDialog.on('confirm', function(response) {
				confirmDialog.close();
				deferred.resolve(response);
			});

			// show the confirmation dialog
			confirmDialog.show();

			deferred.dialog = confirmDialog;
			return deferred;
		},

		confirmForm: function(/*Object*/options) {
			// summary:
			// 		Popup a confirmation dialog containing a `umc.widgets.Form' build from the given widgets
			// options:
			// 		Form form: if not given a `umc.widgets.Form' with the given widgets and layout will be created.
			// 		Object[] widgets: the form widgets
			// 		Object[] layout: the form layout
			// 		String title: the confirmation dialog title (default: 'Confirmation')
			// 		String style: the confirmation dialog css style
			// 		String class: css classes for the confirmation dialog
			// 		Object[] buttons: overwrite the default submit and cancel button
			// 		String submit: the label for the default submit button (default: 'Submit')
			// 		String close: the label for the default cancel button (default: 'Cancel')
			// 		"submit"|"cancel" defaultAction: which default button should be the default? (default: 'submit')
			// 		Object references: if set as empty object, it will be filled with references
			// 		                   to the dialog and form

			// create form
			var form = options.form || new Form({
				widgets: options.widgets,
				layout: options.layout
			});

			// define buttons
			var buttons = options.buttons || [{
				name: 'cancel',
				'default': options.defaultAction == 'cancel',
				label: options.close || _('Cancel')
			}, {
				name: 'submit',
				'default': options.defaultAction != 'cancel',
				label: options.submit || _('Submit')
			}];

			// create confirmation dialog
			var confirmDialog = new ConfirmDialog({
				title: options.title || _('Confirmation'),
				style: options.style || '',
				'class': options['class'] || '',
				message: form,
				options: buttons,
				closable: options.buttons ? options.buttons.length == 1 : true
			});

			// check if the submit button is the default action
			if (array.some(buttons, function(button) { return (button.name === 'submit' && button['default']); })) {
				// confirm the dialog if form was submitted
				form.on('submit', function() {
					confirmDialog.onConfirm('submit');
				});
			}

			var hasSubmitButton = array.some(buttons, function(ibutton) {
				return ibutton.name == 'submit';
			});

			var deferred = new Deferred();
			confirmDialog.on('confirm', function(response) {
				if (!hasSubmitButton || !form.validate || !form.get('value')) {
					// no submit button or no real form -> simply return the response
					deferred.resolve(response);
					confirmDialog.close();
				}
				else if ('submit' === response) {
					if (form.validate()) {
						deferred.resolve(form.get('value'));
						confirmDialog.close();
					}
				} else {
					deferred.cancel({
						button: response,
						values: form.get('value')
					});
					confirmDialog.close();
				}
			});
			// user clicked the x on the top right
			confirmDialog.on('hide', function() {
				if (!deferred.isFulfilled()) {
					deferred.cancel({
						button: null,
						values: form.get('value')
					});
				}
			});

			// show the confirmation dialog
			var showDeferred = confirmDialog.show().then(function() {
				// focus the first widget in the form
				var allWidgets = array.map(options.widgets || [], function(iconf) {
					return form.getWidget(iconf.name);
				});
				var focusableWidgets = array.filter(allWidgets, function(iwidget) {
					return iwidget.focus;
				});
				if (focusableWidgets.length) {
					focusableWidgets[0].focus();
				}
			});

			// return references to widgets if specified in the options
			if ('references' in options) {
				options.references.dialog = confirmDialog;
				options.references.form = form;
				options.references.showDeferred = showDeferred;
			}

			return deferred;
		}
	});

	lang.setObject('umc.dialog', dialog);
	return dialog;
});

