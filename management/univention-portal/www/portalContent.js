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

define([
	"dojo/_base/lang",
	"dojo/Deferred",
	"umc/i18n/tools",
	"umc/tools",
	"umc/dialog",
	"umc/json",
	"umc/store",
	"./links",
	"umc/json!/univention/portal/portal.json", // -> contains entries of this portal as specified in the LDAP directory
	"umc/i18n!portal"
], function(lang, Deferred, i18nTools, tools, dialog, json, store, portalLinks, portalJson, _) {
	var locale = i18nTools.defaultLang().replace(/-/, '_');
	return {
		_portalJson: portalJson,

		reload(admin_mode) {
			var loadDeferred = new Deferred();

			var headers = null;
			if (admin_mode) {
				headers = {
					'X-Univention-Portal-Admin-Mode': 'yes'
				};
			}
			var waitedTime = 0;
			var waitTime = 200;

			var previousPortalJson = lang.clone(this._portalJson);

			var _load = () => {
				if (waitedTime >= 3000) {
					loadDeferred.resolve();
					return;
				}

				setTimeout(() => {
					json.load('/univention/portal/portal.json', require, result => {
						if (result && result.portal && result.entries && result.categories) {
							if (tools.isEqual(result, previousPortalJson)) {
								_load();
							} else {
								this._portalJson = result;
								loadDeferred.resolve();
							}
						} else {
							_load();
						}
					}, headers);
				}, waitTime);
				waitedTime += waitTime;
			};

			_load();
			return loadDeferred;
		},

		logo() {
			return this._portalJson.portal.logo;
		},
		
		background() {
			return this._portalJson.portal.background;
		},

		title() {
			return this._portalJson.portal.name[locale] || this._portalJson.portal.name.en_US || 'Portal';
			// TODO do we want a fallback? we need something that is clickable (as home button)
		},

		portal() {
			return this._portalJson.portal;
		},

		content() {
			let id = 0;
			const toFrontendEntry = (entry, idx, parentDn) => ({
				id: `portalContent_${id++}`,
				idx,
				parentDn,
				type: 'entry',
				dn: entry.dn,
				name: entry.name[locale] || entry.name.en_US,
				description: entry.description[locale] || entry.description.en_US,
				href: portalLinks.getBestLinkAndHostname(entry.links).link,
				bgc: entry.backgroundColor || '',
				logo: entry.logo_name || '/univention/portal/questionMark.svg',
				linkTarget: entry.linkTarget === 'useportaldefault'
					? this._portalJson.portal.defaultLinkTarget
					: entry.linkTarget,
			});

			const toFrontendFolder = (folder, idx, parentDn) => ({
				id: `portalContent_${id++}`,
				idx,
				parentDn,
				type: 'folder',
				dn: folder.dn,
				name: folder.name[locale] || folder.name.en_US,
				entries: folder.entries.map(
					(entryDn, _idx) =>
					toFrontendEntry(this._portalJson.entries[entryDn], _idx, folder.dn)
				),
			});

			const toFrontendCategory = (category, idx) => ({
				id: `portalContent_${id++}`,
				idx,
				dn: category.dn,
				title: category.display_name[locale] || category.display_name.en_US,
				entries: category.entries.map(
					(entryDn, _idx) =>
					entryDn in this._portalJson.entries
					? toFrontendEntry(this._portalJson.entries[entryDn], _idx, category.dn)
					: toFrontendFolder(this._portalJson.folders[entryDn], _idx, category.dn)
				),
			});

			return this._portalJson.portal.categories
				.map((categoryDn, idx) => toFrontendCategory(this._portalJson.categories[categoryDn], idx));
		},

		links() {
			const toFrontendLink = link => ({
				priority: link.$priority,
				dn: link.dn,
				name: link.name[locale] || link.name.en_US,
				description: link.description[locale] || link.description.en_US,
				href: portalLinks.getBestLinkAndHostname(link.links).link,
				logo: link.logo_name || '/univention/portal/questionMark.svg',
				linkTarget: link.linkTarget === 'useportaldefault'
					? this._portalJson.portal.defaultLinkTarget
					: link.linkTarget,
			});
			return {
				user: this._portalJson.user_links.map(link => toFrontendLink(link)),
				misc: this._portalJson.menu_links.map(link => toFrontendLink(link)),
			};
		},




		//// backend
		udmStore() {
			return store('$dn$', 'udm', 'portals/all');
		},

		addCategory(category) {
			const categories = lang.clone(this.portal().categories);
			categories.push(category);
			const deferred = new Deferred();
			this._saveCategories(categories).then(res => {
				if (res.success) {
					dialog.contextNotify(_('Category added to portal'), {type: 'success'});
					deferred.resolve();
				} else {
					dialog.alert(_('Could not add category to portal: %(details)s', res));
					deferred.reject();
				}
			}, () => {
				dialog.alert(_('Could not add category to portal'));
				deferred.reject();
			});
			deferred.then(() => {
				this._publishRefresh();
			});
			return deferred;
		},

		removeCategory(idx) {
			const categories = lang.clone(this.portal().categories);
			categories.splice(idx, 1);
			const deferred = new Deferred();
			this._saveCategories(categories).then(res => {
				if (res.success) {
					dialog.contextNotify(_('Category removed from portal'), {type: 'success'});
					deferred.resolve();
				} else {
					dialog.alert(_('Could not remove category from portal: %(details)s', res));
					deferred.reject();
				}
			}, () => {
				dialog.alert(_('Could not remove category from portal'));
				deferred.reject();
			});
			deferred.then(() => {
				this._publishRefresh();
			});
			return deferred;
		},

		_saveCategories(categories) {
			return this.udmStore().put({
				'$dn$': this.portal().dn,
				categories,
			});
		},

		modify(type, func, params, options = null, parentDn = null) {
			const deferred = new Deferred();
			this.udmStore()[func](params, options).then(res => {
				if (res.success) {
					const message = this._modifyMessage(type, func, true);
					dialog.contextNotify(message, {type: 'success'});
					deferred.resolve(res.$dn$);
				} else {
					const message = this._modifyMessage(type, func, false, res.details)
					dialog.alert(message)
					deferred.reject();
				}
			}, () => {
				const message = this._modifyMessage(type, func, false);
				dialog.alert(message)
				deferred.reject();
			});
			deferred.then(dn => {
				if (func === 'add') {
					if (type === 'category') {
						this.addCategory(dn);
					} else {
						this.addEntry(parentDn, dn);
					}
				} else {
					this._publishRefresh();
				}
			});
			return deferred;
		},
		_modifyMessage(type, func, success, details) {
			if (success) {
				if (func === 'add') {
					return {
						category: _('Created new category'),
						folder: _('Created new folder'),
						entry: _('Created new entry'),
					}[type];
				} else {
					return {
						category: _('Changes to category saved'),
						folder: _('Changes to folder saved'),
						entry: _('Changes to entry saved'),
					}[type];
				}
			} else {
				if (func === 'add') {
					if (details) {
						return {
							category: _('Category could no be created: %s', details),
							folder: _('Folder could not be created: %s', details),
							entry: _('Entry could not be created: %s', details),
						}[type];
					} else {
						return {
							category: _('Category could no be created'),
							folder: _('Folder could not be created'),
							entry: _('Entry could not be created'),
						}[type];
					}
				} else {
					return {
						category: _('Changes to category could no be saved'),
						folder: _('Changes to folder could not be saved'),
						entry: _('Changes to entry could not be saved'),
					}[type];
				}
			}
		},

		removeEntry(parentDn, entryIdx) {
			const parentIsCategory = parentDn in this._portalJson.categories;
			const parent = parentIsCategory
					? this._portalJson.categories[parentDn] : this._portalJson.folders[parentDn];
			const entries = lang.clone(parent.entries);
			entries.splice(entryIdx, 1);

			const deferred = new Deferred();
			this._saveEntries(parentDn, entries).then(res => {
				if (res.success) {
					const msg = parentIsCategory
						? _('Entry removed from category')
						: _('Entry removed from folder');
					dialog.contextNotify(msg, {type: 'success'});
					deferred.resolve();
				} else {
					const msg = parentIsCategory
						? _('Could not remove entry from category: %(details)s', res)
						: _('Could not remove entry from folder: %(details)s', res);
					dialog.alert(msg);
					deferred.reject();
				}
			}, () => {
				const msg = parentIsCategory
					? _('Could not remove entry from category')
					: _('Could not remove entry from folder');
				dialog.alert(msg);
				deferred.reject();
			});
			deferred.then(() => {
				this._publishRefresh();
			});
			return deferred;
		},

		addEntry(parentDn, entryDn) {
			const parentIsCategory = parentDn in this._portalJson.categories;
			const parent = parentIsCategory
					? this._portalJson.categories[parentDn] : this._portalJson.folders[parentDn];
			const entries = lang.clone(parent.entries);
			entries.push(entryDn);

			const deferred = new Deferred();
			this._saveEntries(parentDn, entries).then(res => {
				if (res.success) {
					const msg = parentIsCategory
						? _('Entry added to category')
						: _('Entry added to folder');
					dialog.contextNotify(msg, {type: 'success'});
					deferred.resolve();
				} else {
					const msg = parentIsCategory
						? _('Could not add entry to category: %(details)s', res)
						: _('Could not add entry to folder: %(details)s', res);
					dialog.alert(msg);
					deferred.reject();
				}
			}, () => {
				const msg = parentIsCategory
					? _('Could not add entry to category')
					: _('Could not add entry to folder');
				dialog.alert(msg);
				deferred.reject();
			});
			deferred.then(() => {
				this._publishRefresh();
			});
			return deferred;
		},

		_saveEntries(parentDn, entries) {
			return this.udmStore().put({
				'$dn$': parentDn,
				entries,
			});
		},
		

		_subscribers: [],
		subscribeRefresh(cb) {
			this._subscribers.push(cb);
		},
		_publishRefresh() {
			for (const cb of this._subscribers) {
				cb();
			}
		},
	};
});

