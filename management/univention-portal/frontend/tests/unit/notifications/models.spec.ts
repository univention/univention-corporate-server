/**
 * SPDX-License-Identifier: AGPL-3.0-only
 * SPDX-FileCopyrightText: 2023-2024 Univention GmbH
 */

import * as models from '@/store/modules/notifications/notifications.models';
import { stubFullNotification, stubUuid } from './stubs';

test('token is a uuid string', () => {
  const myNotification: models.FullNotification = {
    ...stubFullNotification,
    token: stubUuid,
  };
  expect(myNotification.token).toBe(stubUuid);
});

test('can be flagged as a backend notification', () => {
  const myNotification: models.FullNotification = {
    ...stubFullNotification,
    isBackendNotification: true,
  };
  expect(myNotification.isBackendNotification).toBe(true);
});
