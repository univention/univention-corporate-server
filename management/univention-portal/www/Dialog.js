/*
 * Copyright 2020 Univention GmbH
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

/**
 * @module portal/Dialog
 */
define([
	"dojo/_base/declare",
	"dojo/dom-class",
	"dijit/Dialog",
	"dijit/_WidgetsInTemplateMixin",
	"umc/tools",
	"umc/widgets/StandbyMixin",
	"umc/widgets/Button",
	"put-selector/put",
	//
	"umc/widgets/ContainerWidget"
], function(declare, domClass, Dialog, _WidgetsInTemplateMixin, tools, StandbyMixin, Button, put) {
	return declare("Dialog", [Dialog, _WidgetsInTemplateMixin, StandbyMixin], {
		//// overwrites
		// dijit/_DialogMixin.js
		actionBarTemplate: '' +
			'<div data-dojo-attach-point="actionBar" class="umcDialogActionBar dijitDisplayNone">' +
				'<div data-dojo-type="umc/widgets/ContainerWidget" data-dojo-attach-point="actionBarLeft"  class="umcDialogActionBarLeft"></div>' +
				'<div data-dojo-type="umc/widgets/ContainerWidget" data-dojo-attach-point="actionBarRight" class="umcDialogActionBarRight"></div>' +
			'</div>',

		// dijit/Dialog.js
		hide() {
			var promise = this.inherited(arguments)
			promise.then(() => {
				if (this.destroyAfterHide) {
					this.destroyRecursive();
				}
			});
			return promise;
		},

		//// self
		destroyAfterHide: false,

		constructor() {
			this.actions = [];
			this.baseClass += ' umcDialog';
		},

		buildRendering() {
			this.inherited(arguments);

			// add widget button to closeButtonNode instead of duplicating styling
			const closeButton = new Button({
				iconClass: 'iconX',
				class: 'ucsIconButton',
				tabindex: -1
			});
			this.closeButtonNode.appendChild(closeButton.domNode);
			closeButton.startup();

			this._updateNoContentClass();
		},

		actions: null,
		_setActionsAttr(actions) {
			this.actionBarLeft.destroyDescendants();
			this.actionBarRight.destroyDescendants();
			for (const action of actions) {
				const align = action.$align || 'right';
				delete action.$align; // FIXME this._set('actions') is now missing $align. does it matter
				const button = new Button(action);
				if (align === 'left') {
					this.actionBarLeft.addChild(button);
				} else {
					this.actionBarRight.addChild(button);
				}
			}
			tools.toggleVisibility(this.actionBar, actions.length > 0);
			this._set('actions', actions);
		},

		wizard: null,
		_setWizardAttr(wizard) {
			this.actionBar.innerHTML = '';
			tools.toggleVisibility(this.actionBar, true);
			const footers = {};
			for (const [name, page] of Object.entries(wizard._pages)) {
				const footer = page._footer;
				tools.toggleVisibility(footer, false);
				put(this.actionBar, footer.domNode);
				footers[name] = page._footer;
			}
			tools.toggleVisibility(footers[wizard.selectedChildWidget.name], true);
			wizard.watch('selectedChildWidget', (_name, oldVal, newVal) => {
				tools.toggleVisibility(footers[oldVal.name], false);
				tools.toggleVisibility(footers[newVal.name], true);
			})
			this._set('wizard', wizard);
		},

		noContentClass: '',
		_updateNoContentClass() {
			domClass.toggle(this.domNode, this.noContentClass, !this.content);
		},

		_setContentAttr(content) {
			this.content = content;
			this.inherited(arguments);
			this._updateNoContentClass();
			this.reposition();
			this._set('content', content);
		},

		reposition() {
			this._relativePosition = null;
			this._position();
		},
	});
});





