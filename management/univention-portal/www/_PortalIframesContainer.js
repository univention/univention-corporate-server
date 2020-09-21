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
 * @module portal/_PortalIframesContainer
 */
define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/dom-class",
	"dojo/topic",
	"dijit/_WidgetBase",
	"dijit/_Container",
	"dijit/_TemplatedMixin",
	"dijit/_WidgetsInTemplateMixin",
	"put-selector/put",
	"./_PortalIframe",
	"umc/tools",
	"umc/i18n!portal",
	//
	"dojox/dtl/tag/logic"
], function(
	declare, lang, domClass, topic, _WidgetBase, _Container, _TemplatedMixin, _WidgetsInTemplateMixin,
	put, _PortalIframe, tools, _
) {
	return declare("_PortalIframesContainer", [_WidgetBase, _Container], {
		selectedIframeId: null,
		_setSelectedIframeIdAttr: function(id) {
			for (const iframeWidget of this.getChildren()) {
				tools.toggleVisibility(iframeWidget, iframeWidget.iframe.id === id);
			}
			this._set('selectedIframeId', id);
		},

		iframes: null,
		_setIframesAttr: function(iframes) {
			const newIframeIds = iframes.map(iframe => iframe.id);
			for (const iframeWidget of this.getChildren()) {
				if (!newIframeIds.includes(iframeWidget.iframe.id)) {
					iframeWidget.destroyRecursive();
				}
			}
			const currentIframeIds = this.getChildren().map(iframeWidget => iframeWidget.iframe.id);
			for (let x = 0; x < iframes.length; x++) {
				const iframe = iframes[x];
				if (!currentIframeIds.includes(iframe.id)) {
					this.addChild(new _PortalIframe({
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


