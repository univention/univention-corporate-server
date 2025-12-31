/*
 * SPDX-FileCopyrightText: 2011-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
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
			this._container = new ContainerWidget({
				'class': 'umcCard2'
			});
			this.addChild(this._container);
		},

		reset: function(contextId, items) {
			this.set('helpText', lang.replace(_('All entries with context {context_id}'), {context_id: '<strong>' + entities.encode(contextId) + '</strong>'}));
			this._contextId = contextId;
			this._container.destroyRecursive();
			this._container = new ContainerWidget({
				'class': 'umcCard2'
			});
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
