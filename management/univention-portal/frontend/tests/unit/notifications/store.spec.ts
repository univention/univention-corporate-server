/**
 * SPDX-License-Identifier: AGPL-3.0-only
 * SPDX-FileCopyrightText: 2023-2024 Univention GmbH
 */

import vuex from 'vuex';

import notifications, {
  actions, defaultHideAfter, mapBackendNotification, mutations, severityMapping,
} from '@/store/modules/notifications';
import { getNotificationsApi } from '@/store/modules/notifications/apiclient';
import { ReceiverApi } from '@/apis/notifications';
import { stubBackendNotification, stubFullNotification, stubUuid } from './stubs';
import * as utils from '../utils';

jest.mock('@/store/modules/notifications/apiclient');
jest.mock('@/apis/notifications');

beforeEach(() => {
  const stubResponse = {
    data: [],
  };
  (ReceiverApi as jest.Mock).mockImplementation(() => ({
    getNotificationsV1NotificationsGet: jest.fn().mockImplementation(() => stubResponse),
    hideNotificationV1NotificationsIdHidePost: jest.fn(),
    deleteNotificationV1NotificationsIdDelete: jest.fn(),
  }));
  utils.mockReturnValue(getNotificationsApi, new ReceiverApi());
});

afterEach(() => {
  jest.resetAllMocks();
});

test('title is set correctly', () => {
  const result = mapBackendNotification(stubBackendNotification);
  expect(result.title).toBe(stubBackendNotification.title);
});

test('description is set correctly', () => {
  const result = mapBackendNotification(stubBackendNotification);
  expect(result.description).toBe(stubBackendNotification.details);
});

test('should set a defaults for link properties if none are submitted', async () => {
  const stubBackend = {
    ...stubBackendNotification,
    link: {
      url: 'https://www.univention.de/',
    },
  };
  const stubStore = new vuex.Store<any>({
    modules: {
      notifications: {
        ...notifications,
        state: {
          notifications: [stubFullNotification],
          backendNotifications: [],
        },
      },
    },
  });

  await stubStore.dispatch('notifications/newBackendNotificationEvent', stubBackend);

  const allNotifications = stubStore.getters['notifications/allNotifications'];
  expect(allNotifications).toHaveLength(2);

  const resultingBackendNotifications = allNotifications.filter((it) => it.isBackendNotification);
  expect(resultingBackendNotifications).toHaveLength(1);

  const resultingNotification = resultingBackendNotifications[0];
  expect(resultingNotification.link.url.toString()).toBe(stubBackend.link.url);
  expect(resultingNotification.link.text).toBe(stubBackend.link.url);
  expect(resultingNotification.link.target).toBe('_blank');
});

test.each([
  [defaultHideAfter, true],
  [-1, false],
])('hidingAfter is set to correctly to %s, popup = %s', (expected, popup) => {
  const stubNotification = {
    ...stubBackendNotification,
    popup,
  };
  const result = mapBackendNotification(stubNotification);
  expect(result.hidingAfter).toBe(expected);
});

test.each(
  Object.entries(severityMapping),
)('importance is set correctly from severity(%s -> %s)', (severity: any, expected) => {
  const notification = {
    ...stubBackendNotification,
    severity,
  };
  const result = mapBackendNotification(notification);
  expect(result.importance).toBe(expected);
});

test.each([
  [true, true],
  [false, false],
  [false, undefined],
])('visible is set %s if popup is %s', (visible, popup) => {
  const stubNotification = {
    ...stubBackendNotification,
    popup,
  };
  const result = mapBackendNotification(stubNotification);
  expect(result.visible).toBe(visible);
});

test('token is set correctly', () => {
  const expectedTokenValue = stubBackendNotification.id;
  const result = mapBackendNotification(stubBackendNotification);
  expect(result.token).toBe(expectedTokenValue);
});

test('backend notifications are flagged with isBackendNotification', () => {
  const result = mapBackendNotification(stubBackendNotification);
  expect(result.isBackendNotification).toBe(true);
});

test('hideNotification commits HIDE_NOTIFICATION', () => {
  const actionContext = {
    commit: jest.fn(),
    dispatch: jest.fn(),
    getters: {
      allNotifications: [stubFullNotification],
    },
    rootState: {
      loadingState: false,
      initialLoadDone: true,
    },
    rootGetters: {},
    state: {
      notifications: [],
      backendNotifications: [],
      api: getNotificationsApi(),
    },
  };
  const token = stubFullNotification.token;
  actions.hideNotification(actionContext, token);
  expect(actionContext.commit).toHaveBeenCalledWith('HIDE_NOTIFICATION', stubFullNotification);
  expect(actionContext.commit).toHaveBeenCalledTimes(1);
});

test('hideNotification commits HIDE_BACKEND_NOTIFICATION', () => {
  const stubNotification = mapBackendNotification(stubBackendNotification);
  const actionContext = {
    commit: jest.fn(),
    dispatch: jest.fn(),
    getters: {
      allNotifications: [stubNotification],
    },
    rootState: {
      loadingState: false,
      initialLoadDone: true,
    },
    rootGetters: {},
    state: {
      notifications: [],
      backendNotifications: [stubBackendNotification],
      api: getNotificationsApi(),
    },
  };
  const token = stubNotification.token;
  actions.hideNotification(actionContext, token);
  expect(actionContext.commit).toHaveBeenCalledWith('HIDE_BACKEND_NOTIFICATION', stubBackendNotification);
  expect(actionContext.commit).toHaveBeenCalledTimes(1);
});

test('hideNotification calls hide on notifications api', async () => {
  const stubBackend = {
    ...stubBackendNotification,
    popup: true,
  };
  const token = stubBackend.id;
  const stubStore = new vuex.Store<any>({
    modules: {
      notifications: {
        ...notifications,
        state: {
          notifications: [],
          backendNotifications: [stubBackend],
          api: getNotificationsApi(),
        },
      },
    },
  });
  expect(stubStore.state.notifications.notifications).toBeDefined();
  await stubStore.dispatch('notifications/hideNotification', token);
  expect(stubStore.state.notifications.api.hideNotificationV1NotificationsIdHidePost).toHaveBeenCalledWith(token);
});

test('HIDE_NOTIFICATION hides local notification', () => {
  const stubNotification = {
    ...stubFullNotification,
    visible: true,
  };
  const stubState = {
    notifications: [],
    backendNotifications: [],
    api: getNotificationsApi(),
  };
  mutations.HIDE_NOTIFICATION(stubState, stubNotification);
  expect(stubNotification.visible).toBe(false);
  expect(stubNotification.hidingAfter).toBe(-1);
});

test('HIDE_BACKEND_NOTIFICATION hides backend notification', () => {
  const stubNotification = {
    ...stubBackendNotification,
    popup: true,
  };
  const stubState = {
    notifications: [],
    backendNotifications: [stubNotification],
    api: getNotificationsApi(),
  };
  mutations.HIDE_BACKEND_NOTIFICATION(stubState, stubNotification);
  expect(stubNotification.popup).toBe(false);
});

test('REMOVE_NOTIFICATION removes local notification', () => {
  const stubState = {
    notifications: [stubFullNotification],
    backendNotifications: [],
    api: getNotificationsApi(),
  };
  mutations.REMOVE_NOTIFICATION(stubState, stubFullNotification);
  expect(stubState.notifications).toHaveLength(0);
});

test('REMOVE_NOTIFICATION does not remove missing local notification', () => {
  const stubState = {
    notifications: [stubFullNotification],
    backendNotifications: [],
    api: getNotificationsApi(),
  };
  const otherFullNotification = {
    ...stubFullNotification,
    token: stubUuid,
  };
  mutations.REMOVE_NOTIFICATION(stubState, otherFullNotification);
  expect(stubState.notifications).toHaveLength(1);
});

test('REMOVE_BACKEND_NOTIFICATION does not remove missing backend notification', () => {
  const stubState = {
    notifications: [],
    backendNotifications: [stubBackendNotification],
    api: getNotificationsApi(),
  };
  const otherBackendNotification = {
    ...stubBackendNotification,
    id: stubUuid,
  };
  mutations.REMOVE_BACKEND_NOTIFICATION(stubState, otherBackendNotification);
  expect(stubState.backendNotifications).toHaveLength(1);
});

test('REMOVE_BACKEND_NOTIFICATION removes backend notification', () => {
  const stubState = {
    notifications: [],
    backendNotifications: [stubBackendNotification],
    api: getNotificationsApi(),
  };
  mutations.REMOVE_BACKEND_NOTIFICATION(stubState, stubBackendNotification);
  expect(stubState.backendNotifications).toHaveLength(0);
});

test('removeNotification commits REMOVE_NOTIFICATION', () => {
  const actionContext = {
    commit: jest.fn(),
    dispatch: jest.fn(),
    getters: {
      allNotifications: [stubFullNotification],
    },
    rootState: {
      loadingState: false,
      initialLoadDone: true,
    },
    rootGetters: {},
    state: {
      notifications: [],
      backendNotifications: [],
      api: getNotificationsApi(),
    },
  };
  const token = stubFullNotification.token;
  actions.removeNotification(actionContext, token);
  expect(actionContext.commit).toHaveBeenCalledWith('REMOVE_NOTIFICATION', stubFullNotification);
  expect(actionContext.commit).toHaveBeenCalledTimes(1);
});

test('removeNotification commits REMOVE_BACKEND_NOTIFICATION', () => {
  const stubNotification = mapBackendNotification(stubBackendNotification);
  const actionContext = {
    commit: jest.fn(),
    dispatch: jest.fn(),
    getters: {
      allNotifications: [stubNotification],
    },
    rootState: {
      loadingState: false,
      initialLoadDone: true,
    },
    rootGetters: {},
    state: {
      notifications: [],
      backendNotifications: [stubBackendNotification],
      api: getNotificationsApi(),
    },
  };
  const token = stubNotification.token;
  actions.removeNotification(actionContext, token);
  expect(actionContext.commit).toHaveBeenCalledWith(
    'REMOVE_BACKEND_NOTIFICATION', stubBackendNotification,
  );
  expect(actionContext.commit).toHaveBeenCalledTimes(1);
});

test('removeNotification calls remove on notifications api', async () => {
  const token = stubBackendNotification.id;
  const stubStore = new vuex.Store<any>({
    modules: {
      notifications: {
        ...notifications,
        state: {
          notifications: [],
          backendNotifications: [stubBackendNotification],
          api: getNotificationsApi(),
        },
      },
    },
  });
  await stubStore.dispatch('notifications/removeNotification', token);
  expect(stubStore.state.notifications.api.deleteNotificationV1NotificationsIdDelete).toHaveBeenCalledWith(token);
});

test('hideAllNotifications hides local and backend notifications', async () => {
  const stubLocal = {
    ...stubFullNotification,
    visible: true,
  };
  const stubBackend = {
    ...stubBackendNotification,
    popup: true,
  };
  const stubStore = new vuex.Store<any>({
    modules: {
      notifications: {
        ...notifications,
        state: {
          notifications: [stubLocal],
          backendNotifications: [stubBackend],
          api: getNotificationsApi(),
        },
      },
    },
  });
  await stubStore.dispatch('notifications/hideAllNotifications');
  const allNotifications = stubStore.getters['notifications/allNotifications'];
  expect(allNotifications).toHaveLength(2);
  allNotifications.forEach((item) => {
    expect(item.visible).toBe(false);
  });
});

test('removeAllNotifications removes local and backend notifications', async () => {
  const stubStore = new vuex.Store<any>({
    modules: {
      notifications: {
        ...notifications,
        state: {
          notifications: [stubFullNotification],
          backendNotifications: [stubBackendNotification],
          api: getNotificationsApi(),
        },
      },
    },
  });
  await stubStore.dispatch('notifications/removeAllNotifications');
  expect(stubStore.state.notifications.notifications).toHaveLength(0);
  expect(stubStore.state.notifications.backendNotifications).toHaveLength(0);
});

test('addWeightedNotification hides notification if bell is open', async () => {
  const stubLocal = {
    ...stubFullNotification,
  };
  const mockHideNotification = jest.fn();
  const stubStore = new vuex.Store<any>({
    getters: {
      'navigation/getActiveButton': () => 'bell',
    },
    modules: {
      notifications: {
        ...notifications,
        actions: {
          ...actions,
          hideNotification: mockHideNotification,
        },
        state: {
          notifications: [],
          backendNotifications: [],
          api: getNotificationsApi(),
        },
      },
    },
  });
  await stubStore.dispatch('notifications/addWeightedNotification', stubLocal);
  expect(mockHideNotification).toHaveBeenCalledTimes(1);
});

test.todo('check the expected behavior of onClick');
