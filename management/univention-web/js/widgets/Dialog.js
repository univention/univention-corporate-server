/*
 * SPDX-FileCopyrightText: 2021-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/aspect",
	"dijit/Dialog",
	"umc/widgets/Button",
	"umc/widgets/StandbyMixin"
], function(declare, lang, aspect, Dialog, Button, StandbyMixin) {
	return declare("umc.widgets.Dialog", [Dialog, StandbyMixin], {
		//// overwrites
		closable: true,

		destroyOnCancel: false,

		hide: function(andDestroy) {
			var promise = this.inherited(arguments);
			if (andDestroy) {
				promise.then(lang.hitch(this, function() {
					this.destroyRecursive();
				}));
			}
			return promise;
		},

		//// self
		close: function() {
			// summary:
			//		Hides the dialog and destroys it after the fade-out animation.
			this.hide(true);
		},

		position: function(forceRecenter) {
			// summary:
			// 		Public function for dijit/Dialog::_position
			// 		Reposition the dialog; centers it if not manually dragged; see dijit/Dialog::_position for more info
			// 		If 'forceRecenter' is true then the dialog is centered even if it were manually positioned before
			if (forceRecenter) {
				this._relativePosition = null;
			}
			this._position();
		},

		//// lifecycle
		buildRendering: function() {
			this.inherited(arguments);
			var closeButton = new Button({
				iconClass: 'x',
				'class': 'ucsIconButton',
				tabindex: -1
			});
			this.closeButtonNode.appendChild(closeButton.domNode);
			closeButton.startup();
		},

		postCreate: function() {
			this.inherited(arguments);
			aspect.before(this, 'onCancel', lang.hitch(this, function() {
				return [this.destroyOnCancel];
			}));
		}
	});
});
