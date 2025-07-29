/*
 * SPDX-FileCopyrightText: 2021-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
import { ActionContext } from 'vuex';

import { PortalModule, RootState } from '../../root.models';
import { FullNotification, Notification, WeightedNotification } from './notifications.models';

export type PortalActionContext<S> = ActionContext<S, RootState>;

export interface Notifications {
  notifications: Array<FullNotification>;
}

const notifications: PortalModule<Notifications> = {
  namespaced: true,
  state: {
    notifications: [],
  },

  mutations: {
    ADD_NOTIFICATION(state: Notifications, notification: FullNotification): void {
      state.notifications.push(notification);
    },
    REMOVE_NOTIFICATION(state: Notifications, notification: FullNotification): void {
      const indexContent = state.notifications.indexOf(notification);
      state.notifications.splice(indexContent, 1);
    },
    HIDE_NOTIFICATION(state: Notifications, notification: FullNotification): void {
      notification.hidingAfter = -1;
      notification.visible = false;
    },
  },
  getters: {
    allNotifications: (state) => state.notifications,
    visibleNotifications: (state) => state.notifications.filter((notification) => notification.visible),
    numNotifications: (state) => state.notifications.length,
  },

  actions: {
    addWeightedNotification({ commit, rootGetters }: PortalActionContext<Notifications>, item: WeightedNotification): void {
      const notification = { ...item, visible: true, token: Math.random() };
      commit('ADD_NOTIFICATION', notification);
      if (rootGetters['navigation/getActiveButton'] === 'bell') {
        commit('HIDE_NOTIFICATION', notification);
      }
    },
    addErrorNotification({ dispatch }: PortalActionContext<Notifications>, item: Notification): void {
      dispatch('addWeightedNotification', { hidingAfter: 4, ...item, importance: 'error' });
    },
    addSuccessNotification({ dispatch }: PortalActionContext<Notifications>, item: Notification): void {
      dispatch('addWeightedNotification', { hidingAfter: 4, ...item, importance: 'success' });
    },
    addNotification({ dispatch }: PortalActionContext<Notifications>, item: Notification): void {
      dispatch('addWeightedNotification', { hidingAfter: 4, ...item, importance: 'default' });
    },
    removeAllNotifications({ commit, getters }: PortalActionContext<Notifications>): void {
      [...getters.allNotifications].forEach((notification) => {
        commit('REMOVE_NOTIFICATION', notification);
      });
    },
    hideAllNotifications({ commit, getters }: PortalActionContext<Notifications>): void {
      getters.visibleNotifications.forEach((notification) => {
        commit('HIDE_NOTIFICATION', notification);
      });
    },
    removeNotification({ commit, getters }: PortalActionContext<Notifications>, token: number): void {
      const notification = getters.allNotifications.find((ntfctn) => ntfctn.token === token);
      if (!notification) {
        return;
      }
      commit('REMOVE_NOTIFICATION', notification);
    },
    hideNotification({ commit, getters }: PortalActionContext<Notifications>, token: number): void {
      const notification = getters.allNotifications.find((ntfctn) => ntfctn.token === token);
      if (!notification) {
        return;
      }
      commit('HIDE_NOTIFICATION', notification);
    },
  },
};

export default notifications;
