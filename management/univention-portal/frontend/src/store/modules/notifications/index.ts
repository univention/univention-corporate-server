/*
 * Like what you see? Join us!
 * https://www.univention.com/about-us/careers/vacancies/
 *
 * Copyright 2021-2024 Univention GmbH
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
import { v4 as uuidv4 } from 'uuid';
import { ActionContext } from 'vuex';

import { ReceiverApi, NotificationRead as BackendNotification, NotificationSeverity } from '@/apis/notifications';

import { PortalModule, RootState } from '../../root.models';
import { FullNotification, Notification, WeightedNotification } from './notifications.models';
import { getNotificationsApi, createEventSource, connectEventListener, EventSource } from './apiclient';

export const defaultHideAfter = 4;

export type PortalActionContext<S> = ActionContext<S, RootState>;

export interface Notifications {
  notifications: Array<FullNotification>;
  backendNotifications: Array<BackendNotification>;
  eventSource?: EventSource;
  api: ReceiverApi;
}

interface DeletedNotificationEvent {
  id: string
}

export const severityMapping = Object.fromEntries([
  [NotificationSeverity.Info, 'default'],
  [NotificationSeverity.Success, 'success'],
  [NotificationSeverity.Warning, 'warning'],
  [NotificationSeverity.Error, 'error'],
]);

const importanceFromSeverity = (severity: NotificationSeverity) => severityMapping[severity];

const generateNotificationToken = () => uuidv4();

export const mapBackendNotification = (notification: BackendNotification): FullNotification => {
  const localNotification: FullNotification = {
    title: notification.title,
    description: notification.details,
    hidingAfter: notification.popup ? defaultHideAfter : -1,
    expireAt: notification.expireTime
      ? new Date(notification.expireTime)
      : null,
    importance: importanceFromSeverity(notification.severity),
    visible: !!notification.popup,
    token: notification.id,
    link: undefined,
    onClick: () => null,
    isBackendNotification: true,
  };
  if (notification.link) {
    localNotification.link = {
      url: new URL(notification.link.url),
      text: notification.link.text ?? notification.link.url,
      target: notification.link.target ?? '_blank',
    };
  }
  return localNotification;
};

const removeFromArray = (array, item) => {
  const indexContent = array.indexOf(item);
  if (indexContent < 0) {
    return;
  }
  array.splice(indexContent, 1);
};

export const mutations = {
  ADD_NOTIFICATION(state: Notifications, notification: FullNotification): void {
    state.notifications.push(notification);
  },
  REMOVE_NOTIFICATION(state: Notifications, notification: FullNotification): void {
    removeFromArray(state.notifications, notification);
  },
  HIDE_NOTIFICATION(state: Notifications, notification: FullNotification): void {
    notification.hidingAfter = -1;
    notification.visible = false;
  },

  SET_BACKEND_NOTIFICATIONS(
    state: Notifications, backendNotifications: Array<BackendNotification>,
  ): void {
    state.backendNotifications = backendNotifications;
  },
  ADD_BACKEND_NOTIFICATION(
    state: Notifications, backendNotification: BackendNotification,
  ): void {
    state.backendNotifications.push(backendNotification);
  },
  UPDATE_BACKEND_NOTIFICATION(
    state: Notifications, newNotification: BackendNotification,
  ): void {
    const id = newNotification.id;
    const index = state.backendNotifications.findIndex((n) => n.id === id);
    if (index < 0) {
      return;
    }
    state.backendNotifications[index] = newNotification;
  },
  REMOVE_BACKEND_NOTIFICATION(
    state: Notifications, backendNotification: BackendNotification,
  ): void {
    removeFromArray(state.backendNotifications, backendNotification);
  },
  HIDE_BACKEND_NOTIFICATION(
    state: Notifications, backendNotification: BackendNotification,
  ): void {
    // TODO: Interim implemented in the UI locally. This will have to be
    // replaced with a call back to the API.
    backendNotification.popup = false;
  },
  SET_EVENT_SOURCE(state: Notifications, eventSource: EventSource): void {
    state.eventSource = eventSource;
  },
  SET_TOKEN(state: Notifications, token?: string): void {
    state.api = getNotificationsApi(token);
  },
};

export const actions = {
  addWeightedNotification({ commit, dispatch, rootGetters }: PortalActionContext<Notifications>, item: WeightedNotification): void {
    const notification = { ...item, visible: true, token: generateNotificationToken() };
    commit('ADD_NOTIFICATION', notification);
    if (rootGetters['navigation/getActiveButton'] === 'bell') {
      dispatch('hideNotification', notification.token);
    }
  },
  addErrorNotification({ dispatch }: PortalActionContext<Notifications>, item: Notification): void {
    dispatch('addWeightedNotification', { hidingAfter: defaultHideAfter, ...item, importance: 'error' });
  },
  addSuccessNotification({ dispatch }: PortalActionContext<Notifications>, item: Notification): void {
    dispatch('addWeightedNotification', { hidingAfter: defaultHideAfter, ...item, importance: 'success' });
  },
  addNotification({ dispatch }: PortalActionContext<Notifications>, item: Notification): void {
    dispatch('addWeightedNotification', { hidingAfter: defaultHideAfter, ...item, importance: 'default' });
  },
  removeAllNotifications({ dispatch, getters }: PortalActionContext<Notifications>): void {
    [...getters.allNotifications].forEach((notification) => {
      dispatch('removeNotification', notification.token);
    });
  },
  hideAllNotifications({ dispatch, getters }: PortalActionContext<Notifications>): void {
    getters.visibleNotifications.forEach((notification) => {
      dispatch('hideNotification', notification.token);
    });
  },
  async removeNotification(
    { commit, getters, state }: PortalActionContext<Notifications>, token: string,
  ): Promise<void> {
    const notification = getters.allNotifications.find((n) => n.token === token);
    if (!notification) {
      return;
    }
    if (notification.isBackendNotification) {
      const backendNotification = state.backendNotifications.find((n) => n.id === token);
      if (backendNotification) {
        commit('REMOVE_BACKEND_NOTIFICATION', backendNotification);
        await state.api.deleteNotificationV1NotificationsIdDelete(backendNotification.id);
      }
    } else {
      commit('REMOVE_NOTIFICATION', notification);
    }
  },
  async hideNotification(
    { commit, getters, state }: PortalActionContext<Notifications>, token: string,
  ): Promise<void> {
    const notification = getters.allNotifications.find((n) => n.token === token);
    if (!notification) {
      return;
    }
    if (notification.isBackendNotification) {
      const backendNotification = state.backendNotifications.find((n) => n.id === token);
      if (backendNotification) {
        commit('HIDE_BACKEND_NOTIFICATION', backendNotification);
        await state.api.hideNotificationV1NotificationsIdHidePost(backendNotification.id);
      }
    } else {
      commit('HIDE_NOTIFICATION', notification);
    }
  },

  async connectNotificationsApi(context: PortalActionContext<Notifications>): Promise<void> {
    await context.dispatch('connectEventStream');
  },
  async fetchNotifications({ commit, state }: PortalActionContext<Notifications>): Promise<void> {
    const response = await state.api.getNotificationsV1NotificationsGet();
    const latestBackendNotifications = response.data;
    commit('SET_BACKEND_NOTIFICATIONS', latestBackendNotifications);
  },
  connectEventStream(context: PortalActionContext<Notifications>): void {
    const connState = context.state.eventSource?.readyState;
    if (([EventSource.CONNECTING, EventSource.OPEN] as Array<number | undefined>).includes(connState)) {
      // browser is automatically reconnecting; nothing to do here
      return;
    }

    const eventSource = createEventSource(context.getters.token);
    context.commit('SET_EVENT_SOURCE', eventSource);

    connectEventListener(
      // default event name 'error': failed to connect event stream
      eventSource, 'error', 'eventStreamErrorEvent', context.dispatch,
    );
    connectEventListener(
      // default event name 'open': event stream connection opened successfully
      eventSource, 'open', 'eventStreamOpenEvent', context.dispatch,
    );
    connectEventListener(
      eventSource, 'new_notification', 'newBackendNotificationEvent', context.dispatch,
    );
    connectEventListener(
      eventSource, 'updated_notification', 'updateBackendNotificationEvent', context.dispatch,
    );
    connectEventListener(
      eventSource, 'deleted_notification', 'deleteBackendNotificationEvent', context.dispatch,
    );
  },
  async eventStreamOpenEvent(context: PortalActionContext<Notifications>): Promise<void> {
    await context.dispatch('fetchNotifications');
  },
  async eventStreamErrorEvent(context: PortalActionContext<Notifications>): Promise<void> {
    console.warn('EventStream connection failed! Reconnecting...');
    await new Promise((res) => { setTimeout(res, 3000); });
    await context.dispatch('connectEventStream');
  },
  newBackendNotificationEvent({ commit, state }: PortalActionContext<Notifications>, eventData: BackendNotification): void {
    const item = state.backendNotifications.find((n) => n.id === eventData.id);
    if (item) {
      console.warn('Received "new_notification" event for an existing notification', eventData);
    } else {
      commit('ADD_BACKEND_NOTIFICATION', eventData);
    }
  },
  updateBackendNotificationEvent({ commit, state }: PortalActionContext<Notifications>, eventData: BackendNotification): void {
    const item = state.backendNotifications.find((n) => n.id === eventData.id);
    if (!item) {
      console.warn('Received "update_notification" event for a non-existing notification', eventData);
    } else {
      commit('UPDATE_BACKEND_NOTIFICATION', eventData);
    }
  },
  deleteBackendNotificationEvent({ commit, state }: PortalActionContext<Notifications>, eventData: DeletedNotificationEvent): void {
    const notification = state.backendNotifications.find((n) => n.id === eventData.id);
    if (!notification) {
      console.warn(
        'Received "delete_notification" event for a non-existing notification', eventData,
      );
    } else {
      commit('REMOVE_BACKEND_NOTIFICATION', notification);
    }
  },
  setAuthToken({ commit }: PortalActionContext<Notifications>, token: string | undefined): void {
    commit('SET_TOKEN', token);
  },
};

export const getters = {
  token: (_state, _getters, _rootState, rootGetters): string | undefined => rootGetters['oidc/token'],
  allNotifications: (state: Notifications): Array<FullNotification> => {
    const backendNotifications : Array<FullNotification> = state.backendNotifications.map(
      (notification) => mapBackendNotification(notification),
    );
    const allNotifications = state.notifications.concat(backendNotifications);
    return allNotifications;
  },
  visibleNotifications: (_state, stateGetters): Array<FullNotification> => (
    stateGetters.allNotifications.filter((notification) => notification.visible)
  ),
  numNotifications: (_state, stateGetters): number => stateGetters.allNotifications.length,
};

const notifications: PortalModule<Notifications> = {
  namespaced: true,
  state: {
    notifications: [],
    backendNotifications: [],
    // TODO: Refactor. This stores an instance of the ReceiverApi with a given token.
    //       When the token changes, the ReceiverApi needs to be instanciated again with the new token.
    //       As with the UMC interface, this should probably go to jsHelper or plugins.
    api: getNotificationsApi(),
  },
  mutations,
  getters,
  actions,
};

export default notifications;
