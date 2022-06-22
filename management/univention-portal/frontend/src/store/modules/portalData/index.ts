/*
 * Copyright 2021-2022 Univention GmbH
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
import { Commit, Dispatch } from 'vuex';
import { put, getAdminState } from '@/jsHelper/admin';
import _ from '@/jsHelper/translate';
import { randomId } from '@/jsHelper/tools';
import { createCategories, doesDescriptionMatch, doesKeywordsMatch, doesFolderMatch, doesTitleMatch } from '@/jsHelper/portalCategories';
import { PortalModule, RootState } from '@/store/root.models';

import setScreenReaderAccouncement from './portalData.helper';
import {
  PortalDataState,
  PortalImageDataBlob,
  LocalizedString,
  PortalContent,
  PortalBaseLayout,
  PortalLayout,
  Position,
  PortalDataActionContext,
  Category,
  TileOrFolder,
} from './portalData.models';

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

function getPosition(layout, id: string, targetIdx: null | number = null, fromPosition: null | Position = null): Position {
  const position: Position = {
    categoryIdx: null,
    folderIdx: null,
    entryIdx: null,
    entryType: null,
    contextType: null,
  };
  for (let categoryIdx = 0; categoryIdx < layout.length; categoryIdx += 1) {
    const category = layout[categoryIdx];
    if (category.id === id) {
      if (targetIdx !== null) {
        position.categoryIdx = categoryIdx;
        position.contextType = 'category';
        position.entryType = 'tile';
        if (targetIdx === -1) {
          if (fromPosition === null) {
            console.warn('fromPosition expected');
          } else {
            // eslint-disable-next-line no-lonely-if
            if (fromPosition.categoryIdx === position.categoryIdx) {
              position.entryIdx = category.tiles.length - 1;
            } else {
              position.entryIdx = category.tiles.length;
            }
          }
        } else {
          position.entryIdx = targetIdx;
        }
      } else {
        position.entryIdx = categoryIdx;
        position.contextType = 'root';
        position.entryType = 'category';
      }

      categoryIdx = layout.length;
      break;
    }
    for (let categoryEntryIdx = 0; categoryEntryIdx < category.tiles.length; categoryEntryIdx += 1) {
      const categoryEntry = category.tiles[categoryEntryIdx];
      if (categoryEntry.id === id) {
        position.categoryIdx = categoryIdx;
        if (targetIdx !== null) {
          position.folderIdx = categoryEntryIdx;
          position.contextType = 'folder';
          position.entryType = 'tile';
          if (targetIdx === -1) {
            if (fromPosition === null) {
              console.warn('fromPosition expected');
            } else {
              // eslint-disable-next-line no-lonely-if
              if (fromPosition.folderIdx === position.folderIdx) {
                position.entryIdx = categoryEntry.tiles.length - 1;
              } else {
                position.entryIdx = categoryEntry.tiles.length;
              }
            }
          } else {
            position.entryIdx = targetIdx;
          }
        } else {
          position.entryIdx = categoryEntryIdx;
          position.contextType = 'category';
          position.entryType = 'tile';
        }

        categoryEntryIdx = category.tiles.length;
        categoryIdx = layout.length;
        break;
      }
      if (categoryEntry.tiles) {
        for (let folderEntryIdx = 0; folderEntryIdx < categoryEntry.tiles.length; folderEntryIdx += 1) {
          const folder = categoryEntry.tiles[folderEntryIdx];
          if (folder.id === id) {
            position.categoryIdx = categoryIdx;
            position.folderIdx = categoryEntryIdx;
            position.entryIdx = folderEntryIdx;
            position.contextType = 'folder';
            position.entryType = 'tile';

            folderEntryIdx = categoryEntry.tiles.length;
            categoryEntryIdx = category.tiles.length;
            categoryIdx = layout.length;
            break;
          }
        }
      }
    }
  }
  return position;
}

function getContext(layout, route: Position): TileOrFolder[] {
  let context = layout;

  if (route.categoryIdx !== null) {
    context = context[route.categoryIdx].tiles;
    if (route.folderIdx !== null) {
      context = context[route.folderIdx].tiles;
    }
  }
  return context;
}

function getLayoutId(layout, position: Position): string {
  const context = getContext(layout, position);
  if (position.entryIdx !== null) {
    return context[position.entryIdx]?.id ?? '';
  }
  return '';
}

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
      baseLayout: {
        layout: [],
        categories: {},
        folders: {},
      },
      layout: [],
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
      state.portal.entries = portal.entries;
      state.portal.folders = portal.folders;
      state.portal.categories = portal.categories.map((c) => {
        c.virtual = c.virtual ?? false;
        return c;
      });
      state.portal.menuLinks = portal.menu_links;
      state.portal.userLinks = portal.user_links;
      if (adminMode) {
        const menu = {
          display_name: {
            en_US: _('Portal Menu'),
          },
          test: 'Portal Menu',
          virtual: true,
          id: '$$menu$$',
          dn: '$$menu$$',
          entries: state.portal.menuLinks,
        };
        const userMenu = {
          display_name: {
            en_US: _('User Menu'),
          },
          test: 'User Menu',
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
      state.portal.baseLayout = {
        layout: state.portal.portal.content.map(([categoryDn]) => categoryDn),
        categories: state.portal.categories.reduce((m, cat) => {
          m[cat.dn] = cat.entries;
          return m;
        }, {}),
        folders: state.portal.folders.reduce((m, folder) => {
          m[folder.dn] = folder.entries;
          return m;
        }, {}),
      };
      state.portal.layout = state.portal.baseLayout.layout.map((categoryDn) => ({
        id: `category-${randomId()}`,
        dn: categoryDn,
        testTitle: categoryDn,
        tiles: state.portal.baseLayout.categories[categoryDn].map((entryDn) => {
          const isFolderDn = entryDn in state.portal.baseLayout.folders;
          if (isFolderDn) {
            return {
              id: `folder-${randomId()}`,
              dn: entryDn,
              tiles: state.portal.baseLayout.folders[entryDn].map((folderDn) => ({
                id: `entry-${randomId()}`,
                dn: folderDn,
              })),
            };
          }
          return {
            id: `entry-${randomId()}`,
            dn: entryDn,
          };
        }),
      }));
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
    SETLAYOUT(state: PortalDataState, payload: {layout: PortalLayout, baseLayout: PortalBaseLayout}): void {
      state.portal.baseLayout = payload.baseLayout;
      state.portal.layout = payload.layout;
    },
    CHANGELAYOUT(state: PortalDataState, payload): void {
      state.portal.baseLayout.layout = payload.content;
      [payload.fromChange, payload.toChange].forEach((change) => {
        if (change.dn) {
          state.portal.baseLayout[change.type][change.dn] = change.entries;
        }
      });
      state.portal.layout = payload.layout;
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
    loaded: (state) => state.cacheId !== '',
    errorContentType: (state) => state.errorContentType,
    portalBaseLayout: (state) => state.portal.baseLayout,
    portalLayout: (state) => state.portal.layout,
    portalFinalLayout: (state, getters) => createCategories(
      getters.portalLayout,
      getters.portalCategories,
      getters.portalEntries,
      getters.portalFolders,
      getters.portalDefaultLinkTarget,
      getters.editMode,
    ),
    portalFinalLayoutFiltered: (state: PortalDataState, getters: any, rootState: RootState, rootGetters: any): Category[] => {
      if (state.editMode) {
        return getters.portalFinalLayout;
      }
      const searchQuery = rootGetters['search/searchQuery'];
      return getters.portalFinalLayout
        .map((category: Category) => {
          category.tiles = category.tiles.filter((entry) => (
            doesTitleMatch(entry, searchQuery) ||
            doesDescriptionMatch(entry, searchQuery) ||
            doesKeywordsMatch(entry, searchQuery) ||
            doesFolderMatch(entry, searchQuery)
          ));
          return category;
        })
        .filter((category: Category) => category.tiles.length > 0);
    },
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
    setLayout({ commit, dispatch }: PortalDataActionContext, layout: {layout: PortalLayout, baseLayout: PortalBaseLayout}): void {
      commit('SETLAYOUT', layout);
      dispatch('changeLayoutUpdateFolder');
    },
    changeLayout({ commit, dispatch, getters }: PortalDataActionContext, payload: { fromId: string, toId: string, position: null | number }): void {
      function move(layout, fromRoute: Position, toRoute: Position): boolean {
        if (fromRoute.entryIdx === null || toRoute.entryIdx === null) {
          return false;
        }

        const fromContext = getContext(layout, fromRoute);
        const toMove = fromContext.splice(fromRoute.entryIdx, 1)[0];

        const toContext = getContext(layout, toRoute);
        toContext.splice(toRoute.entryIdx, 0, toMove);
        return true;
      }

      function orderChange(layout, position: Position) {
        const change = {
          type: '',
          dn: '',
          entries: [],
        };

        if (position.categoryIdx !== null) {
          const category = layout[position.categoryIdx];
          change.type = 'categories';
          change.dn = category.dn;
          change.entries = category.tiles.map((e) => e.dn);
          if (position.folderIdx !== null) {
            const folder = category.tiles[position.folderIdx];
            change.type = 'folders';
            change.dn = folder.dn;
            change.entries = folder.tiles.map((e) => e.dn);
          }
        }
        return change;
      }
      const fromId = payload.fromId;
      const toId = payload.toId;
      if (fromId === toId) {
        dispatch('activity/setMessage', _('Action not possible. Please try another direction.'), { root: true });
        return;
      }
      if (!fromId || !toId) {
        dispatch('activity/setMessage', _('Action not possible. Please try another direction.'), { root: true });
        return;
      }

      const layout = JSON.parse(JSON.stringify(getters.portalLayout));
      const fromPosition = getPosition(layout, fromId, null, null);
      const toPosition = getPosition(layout, toId, payload.position, fromPosition);
      if (
        fromPosition.categoryIdx === toPosition.categoryIdx &&
        fromPosition.folderIdx === toPosition.folderIdx &&
        fromPosition.entryIdx === toPosition.entryIdx
      ) {
        return;
      }
      if (fromPosition.entryType === 'category' && toPosition.entryType === 'category') {
        const toContext = getContext(layout, toPosition);
        const to = toContext[(toPosition.entryIdx as number)];
        if (to.dn === '$$user$$' || to.dn === '$$menu$$') {
          return;
        }
      }

      move(layout, fromPosition, toPosition);

      // update state
      const fromChange = orderChange(layout, fromPosition);
      const toChange = orderChange(layout, toPosition);
      const content = layout.map((cat) => cat.dn);

      const dispatchFunction = (message: string) => {
        dispatch('activity/setMessage', message, { root: true });
      };
      setScreenReaderAccouncement(fromPosition, toPosition, getters.portalFinalLayout, dispatchFunction);

      commit('CHANGELAYOUT', {
        fromChange,
        toChange,
        content,
        layout,
      });

      dispatch('changeLayoutUpdateFolder');
    },
    changeLayoutDirection({ dispatch, getters }: PortalDataActionContext, payload: { fromId: string, direction: 'left' | 'right' | 'up' | 'down'}): void {
      const fromId = payload.fromId;
      const direction = payload.direction;

      const layout = getters.portalLayout;
      const fromPosition = getPosition(layout, fromId);
      const toPosition = { ...fromPosition };
      let position: null | number = null;

      switch (fromPosition.entryType) {
        case 'tile':
          switch (fromPosition.contextType) {
            case 'category':
              switch (direction) {
                case 'left':
                  (toPosition.entryIdx as number) -= 1;
                  break;
                case 'right':
                  (toPosition.entryIdx as number) += 1;
                  break;
                case 'up':
                  toPosition.entryIdx = (toPosition.categoryIdx as number) - 1;
                  toPosition.categoryIdx = null;
                  position = 0;
                  break;
                case 'down':
                  toPosition.entryIdx = (toPosition.categoryIdx as number) + 1;
                  toPosition.categoryIdx = null;
                  position = 0;
                  break;
                default:
                  break;
              }
              break;
            case 'folder':
              switch (direction) {
                case 'left':
                  (toPosition.entryIdx as number) -= 1;
                  break;
                case 'right':
                  (toPosition.entryIdx as number) += 1;
                  break;
                case 'up':
                case 'down':
                default:
                  break;
              }
              break;
            default:
              break;
          }
          break;
        case 'category':
          switch (direction) {
            case 'left':
            case 'right':
              break;
            case 'up':
              (toPosition.entryIdx as number) -= 1;
              break;
            case 'down':
              (toPosition.entryIdx as number) += 1;
              break;
            default:
              break;
          }
          break;
        default:
          break;
      }
      const toId = getLayoutId(layout, toPosition);
      dispatch('changeLayout', {
        fromId,
        toId,
        position,
      });
    },
    async saveLayout({ getters, rootGetters, dispatch }: PortalDataActionContext, payload): Promise<void> {
      let folderPosition: Position | null = null;
      if (rootGetters['modal/getModalComponent']('firstLevelModal') === 'PortalFolder') {
        folderPosition = getPosition(getters.portalLayout, rootGetters['modal/getModalProps']('firstLevelModal').layoutId);
      }
      dispatch('dragndrop/dropped', null, { root: true });
      dispatch('activateLoadingState', null, { root: true });

      const puts: Promise<boolean>[] = [];

      const baseLayout: PortalBaseLayout = getters.portalBaseLayout;

      // folders
      const folders = getters.portalFolders;
      folders.forEach((folder) => {
        const entries = baseLayout.folders[folder.dn];
        if (!isEqual(folder.entries, entries)) {
          puts.push(put(
            folder.dn,
            { entries },
            { dispatch },
            _('Entries could not be re-sorted'),
          ));
        }
      });

      const portalDn = getters.getPortalDn;

      // categories
      const categories = getters.portalCategories;
      categories.forEach((category) => {
        if (category.dn === '$$menu$$' || category.dn === '$$user$$') {
          const field = {
            $$menu$$: 'menuLinks',
            $$user$$: 'userLinks',
          }[category.dn];
          const entries = baseLayout.categories[category.dn];
          if (!isEqual(category.entries, entries)) {
            puts.push(put(
              portalDn,
              { [field]: entries },
              { dispatch },
              _('Entries could not be re-sorted'),
            ));
          }
        } else {
          const entries = baseLayout.categories[category.dn];
          if (!isEqual(category.entries, entries)) {
            puts.push(put(
              category.dn,
              { entries },
              { dispatch },
              _('Entries could not be re-sorted'),
            ));
          }
        }
      });

      // portal content
      const content = getters.portalContent;
      const saved = content.map(([categoryDn]) => categoryDn).filter((categoryDn) => !['$$menu$$', '$$user$$'].includes(categoryDn));
      const current = baseLayout.layout.filter((categoryDn) => !['$$menu$$', '$$user$$'].includes(categoryDn));
      if (!isEqual(saved, current)) {
        puts.push(put(
          portalDn,
          { categories: current },
          { dispatch },
          _('Categories could not be re-sorted'),
        ));
      }
      const results = await Promise.all(puts);
      dispatch('deactivateLoadingState', null, { root: true });
      if (results.length && results.every((result) => !!result)) {
        dispatch('notifications/addSuccessNotification', {
          title: _('Entries successfully re-sorted'),
        }, { root: true });
      }

      if (folderPosition !== null && folderPosition.entryIdx !== null) {
        const folder = getters.portalFinalLayout[folderPosition.categoryIdx as number].tiles[folderPosition.entryIdx as number];
        dispatch('changeLayoutUpdateFolder', folder.layoutId);
        dispatch('activity/setRegion', `${folder.id}-modal-content`, { root: true });
      }
    },
    changeLayoutUpdateFolder({ dispatch, getters, rootGetters }: PortalDataActionContext, folderLayoutId = ''): void {
      if (rootGetters['modal/getModalComponent']('firstLevelModal') === 'PortalFolder') {
        const newLayout = getters.portalFinalLayout;
        const layoutId = folderLayoutId || rootGetters['modal/getModalProps']('firstLevelModal').layoutId;
        let folder;
        newLayout.some((category) => category.tiles.some((entry) => {
          if (entry.layoutId === layoutId) {
            folder = entry;
            return true;
          }
          return false;
        }));
        if (folder) {
          dispatch('modal/changeModalProps', {
            props: {
              tiles: folder.tiles,
              id: `${folder.id}-modal`,
              layoutId: folder.layoutId,
            },
          }, { root: true });
        }
      }
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
        dispatch('activity/setMessage', _('Entered edit mode'), { root: true });
      } else {
        dispatch('activity/setMessage', _('Left edit mode'), { root: true });
      }
    },
    setPortalErrorDisplay({ commit }: { commit: Commit }, payload: number): void {
      commit('PORTAL_DISPLAY_ERROR', payload);
    },
  },
};

export default portalData;
