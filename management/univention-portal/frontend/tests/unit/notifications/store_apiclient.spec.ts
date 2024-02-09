/**
 * SPDX-License-Identifier: AGPL-3.0-only
 * SPDX-FileCopyrightText: 2023-2024 Univention GmbH
 */

import { EventSourcePolyfill } from 'event-source-polyfill';
import * as apiclient from '@/store/modules/notifications/apiclient';

jest.mock('event-source-polyfill');

const EventSource = EventSourcePolyfill;

afterEach(() => {
  jest.resetAllMocks();
});

describe('connectEventSource', () => {

  test('connects to the stream api endpoint', () => {
    const streamUrl = `${apiclient.notificationsApiUrl}/v1/notifications/stream`;
    apiclient.createEventSource();
    expect(EventSource).toHaveBeenCalledWith(streamUrl, { headers: {} });
  });

  test('connects to the stream api endpoint with token', () => {
    const streamUrl = `${apiclient.notificationsApiUrl}/v1/notifications/stream`;
    const authToken = 'foo';
    apiclient.createEventSource(authToken);
    expect(EventSource).toHaveBeenCalledWith(streamUrl, { headers: { Authorization: `Bearer ${authToken}` } });
  });

});
