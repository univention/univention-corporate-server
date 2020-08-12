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
 * @module portal/_PortalIframeTabsContainer
 */
define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/dom-class",
	"dojo/topic",
	"dojo/on",
	"dijit/_WidgetBase",
	"dijit/_Container",
	"dijit/_TemplatedMixin",
	"dijit/_WidgetsInTemplateMixin",
	"dijit/_CssStateMixin",
	"dijit/a11yclick",
	"dijit/form/Button",
	"dojox/dtl/_DomTemplated",
	"put-selector/put",
	"umc/tools",
	"umc/i18n!portal",
	//
	"dojox/dtl/tag/logic"
], function(
	declare, lang, domClass, topic, on, _WidgetBase, _Container, _TemplatedMixin, _WidgetsInTemplateMixin,
	_CssStateMixin, a11yclick, Button, _DomTemplated, put, tools, _
) {

	const IframeTab = declare("_PortalIframeTab", [_WidgetBase, _DomTemplated, _CssStateMixin], {
		baseClass: 'iframeTab',

		widgetsInTemplate: true,
		templateString: `
			<div tabindex="0">
				<div class="iframeTab__background"></div>
				<img
					class="iframeTab__logo"
					src="{{ iframe.logoUrl }}"
					alt="{{ iframe.title }} logo"
				>
				<span class="iframeTab__title">{{ iframe.title }}</span>
				<button
					class="ucsIconButton ucsIconButton--small iframeTab__closeButton"
					data-dojo-type="dijit.form.Button"
					data-dojo-attach-point="closeButton"
					data-dojo-props="
						showLabel: false,
						iconClass: 'iconX'
					"
				></button>
			</div>
		`,

		postCreate: function() {
			this.inherited(arguments);

			on(this.closeButton, 'click', evt => {
				evt.stopPropagation();
				topic.publish('/portal/iframes/close', this.iframe.id);
			});

			on(this.domNode, a11yclick, () => {
				topic.publish('/portal/iframes/select', this.iframe.id);
			});
		},

		// TODO doc
		// required
		iframe: null
	});

	return declare("_PortalIframesContainer", [_WidgetBase, _Container], {
		selectedIframeId: null,
		_setSelectedIframeIdAttr: function(id) {
			for (const iframeWidget of this.getChildren()) {
				iframeWidget.set('selected', iframeWidget.iframe.id === id);
			}
			this._set('selectedIframeId', id);
		},

		iframes: null,
		_setIframesAttr: function(iframes) {
			const newIframeIds = iframes.map(iframe => iframe.id);
			for (const tabWidget of this.getChildren()) {
				if (!newIframeIds.includes(tabWidget.iframe.id)) {
					tabWidget.destroyRecursive();
				}
			}
			const currentIframeIds = this.getChildren().map(tabWidget => tabWidget.iframe.id);
			for (let x = 0; x < iframes.length; x++) {
				const iframe = iframes[x];
				if (!currentIframeIds.includes(iframe.id)) {
					this.addChild(new IframeTab({
						iframe: iframe
					}), x);
				}
			}
			this._set('iframes', iframes);
		},

		constructor: function() {
			this.iframes = [];
		}
	});
});



