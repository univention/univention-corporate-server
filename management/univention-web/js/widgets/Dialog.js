/*
 * Copyright 2021-2022 Univention GmbH
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
