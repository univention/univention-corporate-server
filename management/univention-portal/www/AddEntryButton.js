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
 * @module portal/AddEntryButton
 */
define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/on",
	"dijit/Menu",
	"dijit/MenuItem",
	"dijit/PopupMenuItem",
	"dijit/DropDownMenu",
	"dijit/form/DropDownButton",
	"umc/render",
	"umc/dialog",
	"umc/widgets/Form",
	"./FolderPropertiesDialog",
	"./Dialog",
	"./portalContent",
	"umc/i18n!portal",
], function(declare, lang, on, Menu, MenuItem, PopupMenuItem, DropDownMenu, DropDownButton, render, dialog, Form, FolderPropertiesDialog, Dialog, portalContent, _) {
	// TODO merge with AddExistingFolderDialog (and AddExistingCategoryDialog)
	const AddExistingEntryDialog = declare("AddExistingEntryDialog", [Dialog], {
		//// overwrites
		noContentClass: 'umcDialog--empty',
		title: _('Add entry'),
		destroyAfterHide: true,


		//// self
		parentDn: null, // required

		load: async function() {
			this.standby(true);
			const widgets = [{
				name: 'entry',
				label: _('Folder'),
				dynamicValues: 'udm/syntax/choices',
				dynamicOptions: {
					syntax: 'NewPortalEntries'
				},
				type: 'umc/modules/udm/ComboBox',
				size: 'Two',
				threshold: 2000
			}];
			await render.requireWidgets(widgets);
			this._form = new Form({
				widgets,
				layout: ['entry'],
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
			const entry = this._form.get('value').entry;
			if (!entry) {
				this.hide();
				return;
			}

			this.standby(true);
			portalContent.addEntry(this.parentDn, this._form.get('value').entry).then(() => {
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
	const AddExistingFolderDialog = declare("AddExistingFolderDialog", [Dialog], {
		//// overwrites
		noContentClass: 'umcDialog--empty',
		title: _('Add Folder'),
		destroyAfterHide: true,


		//// self
		parentDn: null, // required

		load: async function() {
			this.standby(true);
			const widgets = [{
				name: 'folder',
				label: _('Folder'),
				dynamicValues: 'udm/syntax/choices',
				dynamicOptions: {
					syntax: 'NewPortalFolders'
				},
				type: 'umc/modules/udm/ComboBox',
				size: 'Two',
				threshold: 2000
			}];
			await render.requireWidgets(widgets);
			this._form = new Form({
				widgets,
				layout: ['folder'],
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
			const folder = this._form.get('value').folder;
			if (!folder) {
				this.hide();
				return;
			}

			this.standby(true);
			portalContent.addEntry(this.parentDn, this._form.get('value').folder).then(() => {
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

	const AddFolderMenu = declare("AddFolderMenu", [DropDownMenu], {
		//// self
		parentDn: null,
		onCreateNewEntry() {},

		//// lifecycle
		buildRendering() {
			this.inherited(arguments);

			const entryMenu = new Menu({});
			entryMenu.addChild(new MenuItem({
				label: _('Create new entry'),
				onClick: () => {
					this.onCreateNewEntry();
				},
			}));
			entryMenu.addChild(new MenuItem({
				label: _('Add existing entry'),
				onClick: () => {
					const dialog = new AddExistingEntryDialog({
						parentDn: this.parentDn,
					});
					dialog.showAndLoad();
				},
			}));

			const folderMenu = new Menu({});
			folderMenu.addChild(new MenuItem({
				label: _('Create new folder'),
				onClick: () => {
					const dialog = new FolderPropertiesDialog({
						parentDn: this.parentDn,
					});
					dialog.showAndLoad();
				},
			}));
			folderMenu.addChild(new MenuItem({
				label: _('Add existing folder'),
				onClick: () => {
					const dialog = new AddExistingFolderDialog({
						parentDn: this.parentDn,
					});
					dialog.showAndLoad();
				},
			}));


			this.addChild(new PopupMenuItem({
				label: _('Add entry'),
				popup: entryMenu,
			}));
			this.addChild(new PopupMenuItem({
				label: _('Add folder'),
				popup: folderMenu,
			}));
		},
	});

	return declare("AddCategoryButton", [DropDownButton], {
		class: 'portalAddEntryButton tile__add',
		// iconClass: 'editMark iconPlus portalAddCategoryButton__icon',

		//// self
		parentDn: null,
		onCreateNewEntry() {},

		//// lifecycle
		postMixInProperties() {
			this.inherited(arguments);
			this.dropDown = new AddFolderMenu({
				parentDn: this.parentDn,
			});
		},

		postCreate() {
			this.inherited(arguments);
			on(this.dropDown, 'createNewEntry', lang.hitch(this, 'onCreateNewEntry'));
		},
	});
});







