/**
 * SPDX-License-Identifier: AGPL-3.0-only
 * SPDX-FileCopyrightText: 2023-2024 Univention GmbH
 */

import { ReceiverApi } from '@/apis/notifications';
import { getNotificationsApi, createEventSource, connectEventListener } from '@/store/modules/notifications/apiclient';
import * as stubs from './stubs';
import * as utils from '../utils';

jest.mock('@/store/modules/notifications/apiclient');
jest.mock('@/apis/notifications');

beforeEach(() => {
  const stubEventSource = stubs.eventSource();
  (createEventSource as jest.Mock).mockReturnValue(stubEventSource);
});

afterEach(() => {
  jest.resetAllMocks();
});

afterAll(() => {
  jest.restoreAllMocks();
});

describe('connectNotificationsApi', () => {

  beforeEach(() => {
    (ReceiverApi as jest.Mock).mockImplementation(() => ({
      getNotificationsV1NotificationsGet: jest.fn().mockImplementation(() => ({ data: [] })),
    }));
  });

  test('connects the event stream', async () => {
    const stubStore = stubs.store();
    const stubToken = undefined;
    await stubStore.dispatch('notifications/connectNotificationsApi');
    expect(createEventSource).toHaveBeenCalledWith(stubToken);
  });

  test('adds EventSource instance into state', async () => {
    const stubStore = stubs.store();
    const stubToken = undefined;
    const stubEventSource = await createEventSource(stubToken);
    await stubStore.dispatch('notifications/connectNotificationsApi');
    expect(stubStore.state.notifications.eventSource).toEqual(stubEventSource);
  });
});

describe('connectEventStream', () => {

  test('connects listeners for the events', async () => {
    const stubStore = stubs.store();
    const stubToken = undefined;
    const stubEventSource = await createEventSource(stubToken);
    await stubStore.dispatch('notifications/connectEventStream');

    expect(connectEventListener).toHaveBeenNthCalledWith(
      1, stubEventSource, 'error', 'eventStreamErrorEvent', expect.anything(),
    );
    expect(connectEventListener).toHaveBeenNthCalledWith(
      2, stubEventSource, 'open', 'eventStreamOpenEvent', expect.anything(),
    );
    expect(connectEventListener).toHaveBeenNthCalledWith(
      3, stubEventSource, 'new_notification', 'newBackendNotificationEvent', expect.anything(),
    );
    expect(connectEventListener).toHaveBeenNthCalledWith(
      4, stubEventSource, 'updated_notification', 'updateBackendNotificationEvent', expect.anything(),
    );
    expect(connectEventListener).toHaveBeenNthCalledWith(
      5, stubEventSource, 'deleted_notification', 'deleteBackendNotificationEvent', expect.anything(),
    );
  });
});

describe('eventStreamOpenEvent', () => {

  test('loads initial notifications from the api', async () => {
    (ReceiverApi as jest.Mock).mockImplementation(() => ({
      getNotificationsV1NotificationsGet: jest.fn().mockImplementation(() => ({ data: [] })),
    }));
    utils.mockReturnValue(getNotificationsApi, new ReceiverApi());

    const stubStore = stubs.store();
    await stubStore.dispatch('notifications/eventStreamOpenEvent');
    expect(stubStore.state.notifications.api.getNotificationsV1NotificationsGet).toHaveBeenCalled();
  });

});

describe('eventStreamErrorEvent', () => {

  test('reconnect the event stream', async () => {
    const stubStore = stubs.store();
    const errorData = { message: 'some error' };
    await stubStore.dispatch('notifications/eventStreamErrorEvent', errorData);
    expect(createEventSource).toHaveBeenCalled();
  });

});

describe('newBackendNotificationEvent', () => {

  test('adds a new backend notification into the state', () => {
    const stubStore = stubs.store();
    const eventData = stubs.stubBackendNotification;
    stubStore.dispatch('notifications/newBackendNotificationEvent', eventData);
    expect(stubStore.state.notifications.backendNotifications).toHaveLength(1);
  });

  test('does not add a known notification into the state', () => {
    const warnMock = jest.spyOn(console, 'warn');
    const stubStore = stubs.store();
    const eventData = stubs.stubBackendNotification;
    stubStore.dispatch('notifications/newBackendNotificationEvent', eventData);
    stubStore.dispatch('notifications/newBackendNotificationEvent', eventData);
    expect(stubStore.state.notifications.backendNotifications).toHaveLength(1);
    expect(warnMock).toHaveBeenCalled();
  });

});

describe('updateBackendNotificationEvent', () => {

  test('updates a backend notification in the store', () => {
    const stubStore = stubs.store();
    const stubNotification = {
      ...stubs.stubBackendNotification,
      popup: true,
    };
    const eventData = {
      ...stubs.stubBackendNotification,
      popup: false,
    };

    // TODO: Refactor: Allow to inject state into stubs.store()
    stubStore.dispatch('notifications/newBackendNotificationEvent', stubNotification);
    expect(stubStore.state.notifications.backendNotifications).toHaveLength(1);

    stubStore.dispatch('notifications/updateBackendNotificationEvent', eventData);
    const backendNotifications = stubStore.state.notifications.backendNotifications;
    expect(backendNotifications).toHaveLength(1);
    expect(backendNotifications[0].popup).toBe(false);
  });

  test('does ignore an event for a non existing backend notification', () => {
    const warnMock = jest.spyOn(console, 'warn');
    const stubStore = stubs.store();
    const eventData = stubs.stubBackendNotification;
    stubStore.dispatch('notifications/updateBackendNotificationEvent', eventData);
    expect(stubStore.state.notifications.backendNotifications).toHaveLength(0);
    expect(warnMock).toHaveBeenCalled();
  });

});

describe('deleteBackendNotificationEvent', () => {

  test('removes a backend notification from the store', () => {
    const stubStore = stubs.store();
    const eventData = {
      id: stubs.stubBackendNotification.id,
    };

    // TODO: Refactor: Allow to inject state into stubs.store()
    stubStore.dispatch('notifications/newBackendNotificationEvent', stubs.stubBackendNotification);
    expect(stubStore.state.notifications.backendNotifications).toHaveLength(1);

    stubStore.dispatch('notifications/deleteBackendNotificationEvent', eventData);
    expect(stubStore.state.notifications.backendNotifications).toHaveLength(0);
  });

  test('does ignore an event for a non existing backend notification', () => {
    const warnMock = jest.spyOn(console, 'warn');
    const stubStore = stubs.store();
    const eventData = {
      id: stubs.stubBackendNotification.id,
    };
    stubStore.dispatch('notifications/deleteBackendNotificationEvent', eventData);
    expect(stubStore.state.notifications.backendNotifications).toHaveLength(0);
    expect(warnMock).toHaveBeenCalled();
  });

});
