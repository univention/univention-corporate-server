/**
 * SPDX-License-Identifier: AGPL-3.0-only
 * SPDX-FileCopyrightText: 2023-2024 Univention GmbH
 */

import { Dispatch } from 'vuex';
import { EventSourcePolyfill } from 'event-source-polyfill';

import { ReceiverApi, Configuration } from '@/apis/notifications';

// Use the polyfill instead of the browser's native EventSource implementation.
// The polyfill allows custom headers (e.g. for Authorization)
// and has consistent reconnecting behavior across browsers.
export const EventSource = EventSourcePolyfill;

export const notificationsApiUrl = process.env.VUE_APP_NOTIFICATIONS_API_URL || './notifications-api';

export const getNotificationsApi = (token?: string): ReceiverApi => new ReceiverApi(
  new Configuration({
    accessToken: token,
    basePath: notificationsApiUrl,
  }),
);

export const createEventSource = (token?: string): EventSource => {
  const streamUrl = `${notificationsApiUrl}/v1/notifications/stream`;

  // send OIDC token if we have it
  const headers = token
    ? { Authorization: `Bearer ${token}` }
    : {};

  const eventSource = new EventSource(streamUrl, { headers });
  return eventSource;
};

export const connectEventListener = (eventSource: EventSource, eventName: string, actionName: string, dispatch: Dispatch): void => {
  eventSource.addEventListener(eventName, (event) => {
    // system events (`open`/`error`) provide no data,
    // while message events come with payload
    const eventData =
      (['open', 'error'].includes(eventName))
        ? undefined
        : JSON.parse((event as MessageEvent).data);
    dispatch(actionName, eventData);
  });
};

export default getNotificationsApi;
