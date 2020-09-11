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
 * @module portal/AddCategoryButton
 */
define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/on",
	"dijit/MenuItem",
	"dijit/DropDownMenu",
	"dijit/form/DropDownButton",
	"umc/render",
	"umc/dialog",
	"umc/widgets/Form",
	"./CategoryPropertiesDialog",
	"./Dialog",
	"./portalContent",
	"umc/i18n!portal",
], function(declare, lang, on, MenuItem, DropDownMenu, DropDownButton, render, dialog, Form, CategoryPropertiesDialog, Dialog, portalContent, _) {
	const AddExistingCategoryDialog = declare("AddExistingCategoryDialog", [Dialog], {
		//// overwrites
		noContentClass: 'umcDialog--empty',
		title: _('Add category'),
		destroyAfterHide: true,


		//// self
		load: async function() {
			this.standby(true);
			const widgets = [{
				name: 'category',
				label: _('Category'),
				dynamicValues: 'udm/syntax/choices',
				dynamicOptions: {
					syntax: 'NewPortalCategories'
				},
				type: 'umc/modules/udm/ComboBox',
				size: 'Two',
				threshold: 2000
			}];
			await render.requireWidgets(widgets);
			this._form = new Form({
				widgets,
				layout: ['category'],
			});
			on(this._form, 'submit', () => {
				this.save();
			});
			await this._form.ready();
			this.set('content', this._form);
			this.standby(false);
		},

		showAndLoad() {
			this.show();
			this.load();
		},

		save() {
			const category = this._form.get('value').category;
			if (!category) {
				this.hide();
				return;
			}

			this.standby(true);
			portalContent.addCategory(this._form.get('value').category).then(() => {
				this.hide();
			}, () => {
				this.standby(false);
			});
		},


		//// lifecycle
		constructor() {
			this.actions = [{
				$align: 'left',
				iconClass: 'iconX',
				class: 'ucsTextButton', 
				label: _('Cancel'),
				onClick: () => {
					this.onCancel();
				},
			}, {
				iconClass: 'iconSave',
				class: 'ucsTextButton',
				label: _('Save'),
				onClick: () => {
					this._form.submit();
				}
			}];
		},
	});

	const AddCategoryMenu = declare("AddCategoryMenu", [DropDownMenu], {
		//// lifecycle
		buildRendering() {
			this.inherited(arguments);
			this.addChild(new MenuItem({
				label: _('Create new category'),
				onClick: () => {
					const dialog = new CategoryPropertiesDialog({});
					dialog.showAndLoad();
				},
			}));
			this.addChild(new MenuItem({
				label: _('Add existing category'),
				onClick: () => {
					const dialog = new AddExistingCategoryDialog({});
					dialog.showAndLoad();
				},
			}));
		},
	});

	return declare("AddCategoryButton", [DropDownButton], {
		class: 'portalAddCategoryButton',
		iconClass: 'editMark iconPlus portal__category__title__editMark',

		//// overwrites
		label: _('Add category'),

		//// lifecycle
		constructor() {
			this.dropDown = new AddCategoryMenu({});
		},

		postCreate() {
			this.inherited(arguments);
		},
	});
});






