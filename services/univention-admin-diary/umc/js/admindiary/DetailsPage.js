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
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/date/locale",
	"dojox/html/entities",
	"put-selector/put",
	"umc/dialog",
	"umc/tools",
	"umc/widgets/Page",
	"umc/widgets/ContainerWidget",
	"umc/widgets/TitlePane",
	"umc/widgets/Form",
	"umc/widgets/MultiSelect",
	"umc/widgets/TextArea",
	"umc/widgets/TextBox",
	"umc/i18n!umc/modules/admindiary"
], function(declare, lang, array, locale, entities, put, dialog, tools, Page, ContainerWidget, TitlePane, Form, MultiSelect, TextArea, TextBox, _) {
	return declare("umc.modules.admindiary.DetailsPage", [ Page ], {

		fullWidth: true,

		postMixInProperties: function() {
			this.inherited(arguments);
			this.headerButtons = [{
				name: 'goto_comment',
				label: _("New Comment"),
				callback: lang.hitch(this, function() {
					this.focusComment();
				})
			}, {
				name: 'close',
				label: _("Back to Diary"),
				callback: lang.hitch(this, function() {
					this.onClose();
				})
			}];
		},

		buildRendering: function() {
			this.inherited(arguments);
			this._container = new ContainerWidget({});
			this.addChild(this._container);
		},

		reset: function(contextId, items) {
			this.set('helpText', lang.replace(_('All entries with context {context_id}'), {context_id: '<strong>' + entities.encode(contextId) + '</strong>'}));
			this._contextId = contextId;
			this._container.destroyRecursive();
			this._container = new ContainerWidget({});
			this.addChild(this._container);
			array.forEach(items, lang.hitch(this, function(item) {
				var node = put(this._container.domNode, 'article.admindiary');
				put(node, 'blockquote.' + item.icon, item.message || 'null');
				put(node, 'address', _('%(username)s on %(hostname)s', item));
				put(node, 'span', locale.format(new Date(item.date)));
			}));
			this._commentForm = new Form({
				widgets: [{
					type: TextArea,
					name: 'message',
					label: _('Comment')
				}],
				layout: ['message'],
				buttons: [{
					name: 'submit',
					label: _('Add comment'),
					callback: lang.hitch(this, '_addComment')
				}]
			});
			this._container.addChild(this._commentForm);
		},

		focusComment: function() {
			this._commentForm.getWidget('message').focus();
		},

		_addComment: function() {
			var values = {
				context_id: this._contextId,
				message: this._commentForm.get('value').message
			};
			this.onNewComment(values);
		},

		onNewComment: function(values) {
		},

		onReload: function(contextId) {
		},

		onClose: function() {
		}
	});
});
