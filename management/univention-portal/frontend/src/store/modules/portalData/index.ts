/*
 * Copyright 2021 Univention GmbH
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
import { Commit, Dispatch, ActionContext } from 'vuex';
import { put, getAdminState } from '@/jsHelper/admin';
import _ from '@/jsHelper/translate';
import { randomId } from '@/jsHelper/tools';

import { PortalModule, RootState } from '../../root.models';
import { PortalData, PortalImageDataBlob, LocalizedString, PortalContent } from './portalData.models';

function isEqual(arr1, arr2) {
  if (arr1.length !== arr2.length) {
    return false;
  }
  return arr1.every((v, i) => v === arr2[i]);
}

interface WaitForChangePayload {
  retries: number;
  adminMode: boolean;
}

export interface PortalDataState {
  portal: PortalData;
  editMode: boolean;
  cacheId: string;
  errorContentType: number | null;
}
type PortalDataActionContext = ActionContext<PortalDataState, RootState>;

const portalData: PortalModule<PortalDataState> = {
  namespaced: true,
  state: {
    portal: {
      portal: {
        name: { en_US: '' },
        background: null,
        defaultLinkTarget: 'embedded',
        dn: 'default',
        categories: [],
        logo: null,
        showUmc: false,
        ensureLogin: false,
        content: [],
      },
      entries: [],
      folders: [],
      categories: [],
      menuLinks: [],
      userLinks: [],
    },
    editMode: getAdminState(),
    cacheId: '',
    errorContentType: null,
  },

  mutations: {
    PORTALDATA(state: PortalDataState, payload): void {
      const portal = payload.portal;
      const adminMode = payload.adminMode;
      state.portal.portal = portal.portal;
      state.portal.entries = portal.entries.map((e) => {
        e.id = `entry-${randomId()}`;
        return e;
      });
      state.portal.folders = portal.folders.map((f) => {
        f.id = `folder-${randomId()}`;
        return f;
      });
      // TODO backend should set virtual
      state.portal.categories = portal.categories.map((c) => {
        c.virtual = c.virtual ?? false;
        c.id = `category-${randomId()}`;
        return c;
      });
      state.portal.menuLinks = portal.menu_links;
      state.portal.userLinks = portal.user_links;
      if (adminMode) {
        const menu = {
          display_name: {
            en_US: _('Portal Menu'),
          },
          virtual: true,
          id: '$$menu$$',
          dn: '$$menu$$',
          entries: state.portal.menuLinks,
        };
        const userMenu = {
          display_name: {
            en_US: _('User Menu'),
          },
          virtual: true,
          id: '$$user$$',
          dn: '$$user$$',
          entries: state.portal.userLinks,
        };
        state.portal.categories.push(userMenu);
        state.portal.categories.push(menu);
        state.portal.portal.content.unshift([userMenu.dn, userMenu.entries]);
        state.portal.portal.content.unshift([menu.dn, menu.entries]);
      }
      state.cacheId = portal.cache_id;
    },
    PORTALNAME(state: PortalDataState, name: LocalizedString): void {
      state.portal.portal.name = name;
    },
    PORTALLOGO(state: PortalDataState, data: PortalImageDataBlob): void {
      state.portal.portal.logo = data;
    },
    CONTENT(state: PortalDataState, content: PortalContent): void {
      state.portal.portal.content = content;
    },
    PORTALBACKGROUND(state: PortalDataState, data:PortalImageDataBlob): void {
      state.portal.portal.background = data;
    },
    CHANGE_FOLDER_ENTRIES(state: PortalDataState, payload): void {
      state.portal.folders.forEach((folder) => {
        if (folder.dn !== payload.dn) {
          return;
        }
        folder.entries = payload.entries;
      });
    },
    CHANGE_CATEGORY(state: PortalDataState, payload): void {
      state.portal.categories.forEach((category) => {
        if (category.dn !== payload.category) {
          return;
        }
        category.entries = payload.entries;
      });
    },
    RESHUFFLE_CATEGORY(state: PortalDataState, payload): void {
      state.portal.portal.content = state.portal.portal.content.map(([category, entries]) => {
        if (category === payload.category) {
          return [category, payload.entries];
        }
        return [category, entries];
      });
    },
    EDITMODE(state: PortalDataState, editMode: boolean): void {
      state.editMode = editMode;

      // save state to localstorage if we are in dev mode
      if (process.env.VUE_APP_LOCAL) {
        if (editMode) {
          // console.info('logged into admin mode');
          localStorage.setItem('UCSAdmin', editMode.toString());
        } else {
          // console.info('logged out of admin mode');
          localStorage.removeItem('UCSAdmin');
        }
      }
    },
    PORTAL_DISPLAY_ERROR(state: PortalDataState, payload: number): void {
      state.errorContentType = payload;
    },
  },

  getters: {
    getPortal: (state) => state.portal,
    getPortalDn: (state) => state.portal.portal.dn,
    portalName: (state) => state.portal.portal.name,
    portalLogo: (state) => state.portal.portal.logo,
    portalBackground: (state) => state.portal.portal.background,
    portalShowUmc: (state) => state.portal.portal.showUmc,
    portalEnsureLogin: (state) => state.portal.portal.ensureLogin,
    portalContent: (state) => state.portal.portal.content,
    portalEntries: (state) => state.portal.entries,
    portalFolders: (state) => state.portal.folders,
    portalCategories: (state) => state.portal.categories,
    portalCategoriesOnPortal: (state) => state.portal.portal.categories,
    portalDefaultLinkTarget: (state) => state.portal.portal.defaultLinkTarget,
    userLinks: (state) => state.portal.userLinks,
    menuLinks: (state) => state.portal.menuLinks,
    editMode: (state) => state.editMode,
    cacheId: (state) => state.cacheId,
    errorContentType: (state) => state.errorContentType,
  },

  actions: {
    setPortal({ commit }: PortalDataActionContext, payload): void {
      commit('PORTALDATA', payload);
    },
    setPortalName({ commit }: PortalDataActionContext, name: LocalizedString): void {
      commit('PORTALNAME', { ...name });
    },
    setPortalLogo({ commit }: PortalDataActionContext, data: PortalImageDataBlob): void {
      commit('PORTALLOGO', data);
    },
    setPortalBackground({ commit }: PortalDataActionContext, data: PortalImageDataBlob): void {
      commit('PORTALBACKGROUND', data);
    },
    async savePortalCategories({ dispatch, getters }: PortalDataActionContext): Promise<void> {
      const content = getters.portalContent;
      const portalDn = getters.getPortalDn;
      const attrs = {
        categories: content.map(([category]) => category).filter((category) => !['$$menu$$', '$$user$$'].includes(category)),
      };
      await put(portalDn, attrs, { dispatch }, _('Categories could not be re-sorted'), _('Categories successfully re-sorted'));
    },
    async saveFolder({ getters, dispatch }: PortalDataActionContext, payload): Promise<void> {
      const folder = getters.portalFolders.find((foldr) => foldr.dn === payload.dn);
      if (!folder) {
        return;
      }
      const attrs = {
        entries: folder.entries,
      };
      // console.info('Rearranging entries for', payload.dn);
      await put(folder.dn, attrs, { dispatch }, _('Entries could not be re-sorted'), _('Entries successfully re-sorted'));
    },
    async saveContent({ dispatch, getters }: PortalDataActionContext): Promise<void> {
      const content = getters.portalContent;
      const categories = getters.portalCategories;
      const portalDn = getters.getPortalDn;
      const puts: Promise<boolean>[] = [];
      content.forEach(([cat, entries]) => {
        if (cat === '$$user$$') {
          // console.info('Rearranging entries for user menu');
          const attrs = {
            userLinks: entries,
          };
          const ret = put(portalDn, attrs, { dispatch }, _('Entries could not be re-sorted'));
          puts.push(ret);
          return;
        }
        if (cat === '$$menu$$') {
          // console.info('Rearranging entries for portal menu');
          const attrs = {
            menuLinks: entries,
          };
          const ret = put(portalDn, attrs, { dispatch }, _('Entries could not be re-sorted'));
          puts.push(ret);
          return;
        }
        categories.forEach((category) => {
          if (cat !== category.dn) {
            return;
          }
          const attrs = {
            entries,
          };
          if (isEqual(entries, category.entries)) {
            return;
          }
          // console.info('Rearranging entries for', cat);
          const ret = put(cat, attrs, { dispatch }, _('Entries could not be re-sorted'));
          puts.push(ret);
        });
      });
      const results = await Promise.all(puts);
      if (results.every((result) => !!result)) {
        dispatch('notifications/addSuccessNotification', {
          title: _('Entries successfully re-sorted'),
        }, { root: true });
      }
    },
    replaceContent({ commit }: PortalDataActionContext, content: Array<Record<string, unknown>>): void {
      commit('CONTENT', content);
    },
    moveContent({ commit, getters }: PortalDataActionContext, payload): void {
      const src = payload.src;
      const origin = payload.origin;
      const dst = payload.dst;
      const cat = payload.cat;
      const content = getters.portalContent.map(([category, oldEntries]) => {
        if (category === origin) {
          const entries = [...oldEntries];
          const idx = entries.indexOf(src);
          entries.splice(idx, 1);
          return [category, entries];
        }
        if (category === cat) {
          const entries = [...oldEntries];
          let idx = entries.indexOf(dst);
          if (idx === -1) {
            // TileAdd.vue
            idx = entries.length;
          }
          entries.splice(idx, 0, src);
          return [category, entries];
        }
        return [category, oldEntries];
      });
      commit('CONTENT', content);
    },
    reshuffleContent({ commit, dispatch, rootGetters, getters }: PortalDataActionContext, payload): void {
      const src = payload.src;
      const dst = payload.dst;
      const cat = payload.cat;
      const content = getters.portalContent;
      if (!cat) {
        // src and dst are categories!
        const newContent: string[][] = [];
        let srcContent: string[] = [];
        let srcIdx = -1;
        let dstContent: string[] = []; // TODO
        let dstIdx = -1;
        content.forEach(([category, entries], idx) => {
          if (category === src) {
            srcContent = [category, entries];
            srcIdx = idx;
          }
          if (category === dst) {
            dstContent = [category, entries];
            dstIdx = idx;
          }
        });
        if (srcIdx < dstIdx) {
          newContent.push(...content.slice(0, srcIdx));
          newContent.push(...content.slice(srcIdx + 1, dstIdx + 1));
          newContent.push(srcContent);
          newContent.push(...content.slice(dstIdx + 1));
        } else {
          newContent.push(...content.slice(0, dstIdx));
          newContent.push(srcContent);
          newContent.push(...content.slice(dstIdx, srcIdx));
          newContent.push(...content.slice(srcIdx + 1));
        }
        commit('CONTENT', newContent);
        return;
      }
      const catIsFolder = getters.portalFolders.some((foldr) => foldr.dn === cat);
      if (catIsFolder) {
        getters.portalFolders.forEach((folder) => {
          if (folder.dn !== cat) {
            return;
          }
          const entries: string[] = [];
          const tiles: Array<Record<string, unknown>> = [];
          const srcIdx = folder.entries.indexOf(src);
          let dstIdx = folder.entries.indexOf(dst);
          const oldTiles = [...rootGetters['modal/getModalProps']('firstLevelModal').tiles];
          if (dstIdx === -1) {
            // TileAdd.vue
            dstIdx = oldTiles.length - 1;
          }
          if (srcIdx < dstIdx) {
            entries.push(...folder.entries.slice(0, srcIdx));
            entries.push(...folder.entries.slice(srcIdx + 1, dstIdx + 1));
            entries.push(src);
            entries.push(...folder.entries.slice(dstIdx + 1));
            tiles.push(...oldTiles.slice(0, srcIdx));
            tiles.push(...oldTiles.slice(srcIdx + 1, dstIdx + 1));
            tiles.push(oldTiles[srcIdx]);
            tiles.push(...oldTiles.slice(dstIdx + 1));
          } else {
            entries.push(...folder.entries.slice(0, dstIdx));
            entries.push(src);
            entries.push(...folder.entries.slice(dstIdx, srcIdx));
            entries.push(...folder.entries.slice(srcIdx + 1));
            tiles.push(...oldTiles.slice(0, dstIdx));
            tiles.push(oldTiles[srcIdx]);
            tiles.push(...oldTiles.slice(dstIdx, srcIdx));
            tiles.push(...oldTiles.slice(srcIdx + 1));
          }
          commit('CHANGE_FOLDER_ENTRIES', {
            dn: cat,
            entries,
          });
          dispatch('modal/changeModalProps', {
            props: {
              tiles,
            },
          }, { root: true });
        });
        return;
      }
      content.forEach(([category, oldEntries]) => {
        if (category !== cat) {
          return;
        }
        const idx1 = oldEntries.indexOf(src);
        let idx2 = oldEntries.indexOf(dst);
        if (idx2 === -1) {
          // TileAdd.vue
          idx2 = oldEntries.length - 1;
          if (idx1 === idx2) {
            // otherwise drop does not work on TileAdd.vue
            // I do not know exactly why, though
            return;
          }
        }
        let entries: string[] = [];
        if (idx1 < idx2) {
          entries = oldEntries.slice(0, idx1);
          entries = entries.concat(oldEntries.slice(idx1 + 1, idx2 + 1));
          entries.push(src);
          entries = entries.concat(oldEntries.slice(idx2 + 1));
        } else {
          entries = oldEntries.slice(0, idx2);
          entries.push(src);
          entries = entries.concat(oldEntries.slice(idx2, idx1));
          entries = entries.concat(oldEntries.slice(idx1 + 1));
        }
        commit('RESHUFFLE_CATEGORY', { category, entries });
      });
    },
    async waitForChange({ dispatch, getters }: PortalDataActionContext, payload: WaitForChangePayload): Promise<boolean | void> {
      if (payload.retries <= 0) {
        return false;
      }
      const response = await dispatch('portalJsonRequest', { adminMode: payload.adminMode }, { root: true });
      const portalJson = response.data;
      if (portalJson.cache_id !== getters.cacheId) {
        return true;
      }
      await new Promise((resolve) => {
        setTimeout(resolve, 1000);
      });
      payload.retries -= 1;
      return dispatch('waitForChange', payload);
    },
    async setEditMode({ dispatch, commit }: { commit: Commit, dispatch: Dispatch }, editMode: boolean): Promise<void> {
      commit('EDITMODE', editMode);
      dispatch('dragndrop/dropped', null, { root: true });
      await dispatch('loadPortal', { adminMode: editMode }, { root: true });
      if (editMode) {
        dispatch('activity/addMessage', {
          id: 'editmode',
          msg: _('Entered edit mode'),
        }, { root: true });
      } else {
        dispatch('activity/addMessage', {
          id: 'editmode',
          msg: _('Left edit mode'),
        }, { root: true });
      }
    },
    setPortalErrorDisplay({ commit }: { commit: Commit }, payload: number): void {
      commit('PORTAL_DISPLAY_ERROR', payload);
    },
  },
};

export default portalData;
