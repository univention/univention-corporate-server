/*
 * Copyright 2011-2019 Univention GmbH
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
/*global define,setTimeout*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/dom-class",
	"dojox/html/entities",
	"dijit/ProgressBar",
	"umc/tools",
	"umc/dialog",
	"umc/widgets/ContainerWidget",
	"umc/widgets/Text",
	"umc/i18n!"
], function(declare, lang, array, domClass, entities, ProgressBar, tools, dialog, ContainerWidget, Text, _) {
	return declare("umc.widgets.ProgressBar", ContainerWidget, {
		// summary:
		//		This class provides a widget providing detailed progress information
		baseClass: 'umcProgressBar',

		allowHTMLErrors: false,

		_component: null,
		_message: null,
		_progressBar: null,
		_errors: null,
		_criticalError: null,

		_initialComponent: null,
		umcpCommand: lang.hitch(tools, 'umcpCommand'),

		buildRendering: function() {
			this.inherited(arguments);

			this._component = new Text({
				content : '',
				'class': 'umcProgressBarComponent'
			});
			this.addChild(this._component);
			this._progressBar = new ProgressBar({});
			this.addChild(this._progressBar);
			this._message = new Text({
				content : '&nbsp;',
				'class': 'umcProgressBarMessage'
			});
			this.addChild(this._message);

			this._progressBar.set('value', 0);
			this._progressBar.set('maximum', 100);

			this._progressBar.watch('value', lang.hitch(this, function(attr, oldValue, newValue) {
				// looks buggy when setting value to Infinity and then back to 0
				//   (like going backwards). Used in App Center; Bug #32649
				var comesFromOrGoesToInfinity = oldValue === Infinity || newValue === Infinity;
				domClass.toggle(this.domNode, 'noTransition', comesFromOrGoesToInfinity);
			}));

			this.reset();
			this.startup();
		},

		reset: function(initialComponent) {
			if (initialComponent) {
				this._initialComponent = initialComponent;
			}
			this._criticalError = false;
			this._errors = [];

			this._component.set('content', entities.encode(this._initialComponent));

			// make sure that at least a not breakable space is printed
			// ... this avoids vertical jumping of widgets
			this._message.set('content', '&nbsp;');

			this._progressBar.set('value', 0);
		},

		setInfo: function(component, message, percentage, errors, critical) {
			if (component) {
				this._component.set('content', entities.encode(component));
			}
			if (percentage) {
				this._progressBar.set('value', percentage);
			}
			if (message || component) {
				this._message.set('content', entities.encode(message) || '&nbsp;');
			}
			this._addErrors(errors);
			if (critical) {
				this._criticalError = true;
			}
		},

		_addErrors: function(errors) {
			array.forEach(errors, lang.hitch(this, function(error) {
				if (error) {
					if (array.indexOf(this._errors, error) === -1) {
						this._errors.push(error);
					}
				}
			}));
		},

		feedFromDeferred: function(deferred, msg) {
			this.reset(msg);
			if (deferred._lastProgress) {
				// missed the first few updates?
				var result = deferred._lastProgress;
				this.setInfo(result.component, result.message, result.percentage, result.errors, result.critical);
			}
			deferred.then(
				undefined, // resolve()
				undefined, // cancel()
				lang.hitch(this, function(result) { // progress()
					this.setInfo(result.component, result.message, result.percentage, result.errors, result.critical);
				})
			);
		},

		auto: function(umcpCommand, umcpOptions, callback, pollErrorMsg, stopComponent, dontHandleErrors, untilDeferred) {
			if (untilDeferred && untilDeferred.isFulfilled()) {
				// auto caught SIGTERM !
				this.stop(callback, stopComponent, !dontHandleErrors);
				return;
			}
			if (pollErrorMsg === undefined) {
				pollErrorMsg = _('Fetching information from the server failed!');
			}
			this.umcpCommand(umcpCommand,
				umcpOptions, undefined, undefined,
				{
					messageInterval: 30,
					message: pollErrorMsg,
					xhrTimeout: 40
				}
			).then(lang.hitch(this, function(data) {
				var result = data.result;
				if (result) {
					this.setInfo(result.component, result.info, result.steps, result.errors, result.critical);
					if (!result.finished) {
						setTimeout(lang.hitch(this, 'auto', umcpCommand, umcpOptions, callback, pollErrorMsg, stopComponent, dontHandleErrors, untilDeferred), 200);
					}
				}
				if (!result || result.finished) {
					this.stop(callback, stopComponent, !dontHandleErrors);
				}
			}));
		},

		stop: function(callback, stopComponent, handleErrors) {
			var errors = this.getErrors().errors;
			if (errors.length && handleErrors) {
				var msg = '';
				if (errors.length === 1) {
					msg = _('An error occurred: ') + this._encodeError(errors[0]);
				} else {
					msg = lang.replace(_('{number} errors occurred: '), {number : errors.length});
					msg += '<ul><li>' + array.map(errors, lang.hitch(this, '_encodeError')).join('</li><li>') + '</li></ul>';
				}
				dialog.confirm(msg, [{
					label: 'Ok',
					'default': true,
					callback: callback
				}]);
			} else {
				callback();
			}
		},

		_encodeError: function(error) {
			if (!this.allowHTMLErrors) {
				error = entities.encode(error);
			}
			return error;
		},

		getErrors: function() {
			return {'errors' : this._errors, 'critical' : this._criticalError};
		}
	});
});
