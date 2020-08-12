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
 * @module portal/_PortalIframe
 */
define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/topic",
	"dijit/_WidgetBase",
	"dojox/dtl/_DomTemplated",
	"put-selector/put",
	"umc/tools",
	"umc/i18n!portal",
	//
	"dojox/dtl/tag/logic"
], function(declare, lang, topic, _WidgetBase, _DomTemplated, put, tools, _) {
	return declare("_PortalIframe", [_WidgetBase, _DomTemplated], {
		templateString: `
			<div class="portalIframe">
				<span
					class="portalIframe__status"
					data-dojo-attach-point="statusNode"
				></span>
				<iframe 
					class="portalIframe__iframe"
					src="{{ iframe.url }}"
					data-dojo-attach-point="iframeNode"
				></iframe>
			</div>
		`,

		// TODO doc
		// required
		iframe: null,

		status: 'loading',
		_setStatusAttr: function(status) {
			switch (status) {
				case 'loading':
					this.statusNode.innerHTML = '';
					put(this.statusNode, '.loadingSpinner.loadingSpinner--visible');
					tools.toggleVisibility(this.statusNode, true);
					break;
				case 'error':
					this.statusNode.innerHTML = _('Content could not be loaded.');
					put(this.statusNode, '!loadingSpinner!loadingSpinner--visible');
					tools.toggleVisibility(this.statusNode, true);
					break;
				case 'loaded':
					put(this.statusNode, '!loadingSpinner!loadingSpinner--visible');
					tools.toggleVisibility(this.statusNode, false);
					break;
			}
			this._set('status', status);
		},

		postCreate: function() {
			// you can't open iframes with src http (no 's')
			// when the origin is https.
			// This is a 'Mixed Content' error and it can't be catched
			// (as far as i know).
			// So we say that an iframe failed when onload does not fire
			// after 4 seconds.
			const maybeLoadFailed = setTimeout(() => {
				this.set('status', 'error');
			}, 4000);

			this.iframeNode.addEventListener('load', () => {
				this.set('status', 'loaded');
				clearTimeout(maybeLoadFailed);

				// try to get the pathname of the iframe location.
				// This will not always work if the portal and iframe are not of same origin
				const pathname = lang.getObject('contentWindow.location.pathname', false, this.iframeNode);
				if (pathname === '/univention/portal' || pathname === '/univention/portal/') {
					topic.publish('/portal/iframes/remove', id);
				}

				try {
					this.iframeNode.contentWindow.addEventListener('beforeunload', () => {
						this.set('status', 'loading');
					});
				} catch(e) {}
			});

			this.iframeNode.addEventListener('error', () => {
				this.set('status', 'error');
			});
		}
	});
});



