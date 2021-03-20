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
import { FullNotification, Notification, WeightedNotification } from '../models';
import { PortalModule } from '../types';

export interface NotificationBubbleState {
  visible: boolean;
  visibleStandalone: boolean;
  visibleNew: boolean;
  content: Array<FullNotification>;
  contentOfNewNotification: Array<FullNotification>;
}

const notificationBubble: PortalModule<NotificationBubbleState> = {
  namespaced: true,
  state: {
    visible: false,
    visibleStandalone: false,
    visibleNew: false,
    content: [],
    contentOfNewNotification: [],
  },

  mutations: {
    WRITE_CONTENT(state, payload) {
      state.content = payload;
    },
    ADD_CONTENT(state, notification: FullNotification) {
      state.contentOfNewNotification = [];
      state.content.push(notification);
      state.contentOfNewNotification.push(notification);
    },
    SHOW(state) {
      state.visibleStandalone = true;
    },
    SHOW_NEW(state) {
      state.visibleNew = true;
    },
    SHOW_EMBEDDED(state) {
      state.visible = true;
      state.visibleStandalone = false;
      state.visibleNew = false;
    },
    HIDE(state) {
      state.visibleStandalone = false;
    },
    HIDE_NEW_NOTIFICATION(state) {
      state.visibleNew = false;
    },
    HIDE_ALL_NOTIFICATIONS(state) {
      state.visible = false;
      state.visibleStandalone = false;
      state.visibleNew = false;
    },
    DELETE_SINGLE_NOTIFICTION(state, token) {
      const indexContent = state.content.findIndex((notification) => notification.bubbleToken === token);
      const indexNewNotification = state.contentOfNewNotification.findIndex((notification) => notification.bubbleToken === token);
      state.content.splice(indexContent, 1);
      state.contentOfNewNotification.splice(indexNewNotification, 1);
    },
  },
  getters: {
    bubbleState: (state) => state.visible,
    bubbleStateStandalone: (state) => state.visibleStandalone,
    bubbleStateNewBubble: (state) => state.visibleNew,
    bubbleContent: (state) => state.content,
    bubbleContentNewNotification: (state) => state.contentOfNewNotification,
  },

  actions: {
    setShowBubble({ commit }, payload) {
      commit('SHOW', payload);
    },
    setShowNewBubble({ commit }, payload) {
      commit('SHOW_NEW', payload);
    },
    setHideBubble({ commit }, payload) {
      commit('HIDE', payload);
    },
    setHideNewBubble({ commit }) {
      commit('HIDE_NEW_NOTIFICATION');
    },
    setContent({ commit }, payload) {
      commit('WRITE_CONTENT', payload);
    },
    addContent({ commit }, item: WeightedNotification) {
      commit('ADD_CONTENT', { ...item, bubbleToken: Math.random() });
      commit('SHOW_NEW');
    },
    addNotification({ dispatch }, item: Notification) {
      dispatch('addContent', { ...item, bubbleImportance: 'neutral' });
    },
    hideAllNotifications({ commit }, payload) {
      commit('HIDE_ALL_NOTIFICATIONS', payload);
    },
    showEmbedded({ commit }, payload) {
      commit('SHOW_EMBEDDED', payload);
    },
    deleteSingleNotification({ commit }, token) {
      commit('DELETE_SINGLE_NOTIFICTION', token);
    },
  },
};

export default notificationBubble;
