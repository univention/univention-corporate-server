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
import addLanguageTile from '@/jsHelper/addLanguageTile';
import createMenuStructure from '@/jsHelper/createMenuStructure';
import createUserMenu from '@/jsHelper/createUserMenu';
import { PortalModule } from '@/store/root.models';

export interface MenuState {
  menu: Array<unknown>;
  disabled: Array<string>;
}

const menu: PortalModule<MenuState> = {
  namespaced: true,
  state: {
    menu: [],
    disabled: [],
  },

  mutations: {
    MENU(state, payload) {
      const menuStructure = createMenuStructure(payload.portal);
      const languageMenuLink = addLanguageTile(payload.availableLocales);
      const userLinks = createUserMenu(payload.portal);
      if (languageMenuLink) {
        menuStructure.unshift(languageMenuLink);
      }
      if (userLinks) {
        menuStructure.unshift(userLinks);
      }
      state.menu = menuStructure;
    },
    DISABLED(state, payload) {
      state.disabled = payload;
    },
  },

  getters: {
    getMenu: (state) => state.menu,
    disabledMenuItems: (state) => state.disabled,
  },

  actions: {
    setMenu({ commit }, payload) {
      commit('MENU', payload);
    },
    setDisabled({ commit }, payload) {
      commit('DISABLED', payload);
    },
  },
};

export default menu;
