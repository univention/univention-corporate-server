/**
 * SPDX-License-Identifier: AGPL-3.0-only
 * SPDX-FileCopyrightText: 2023-2024 Univention GmbH
 */

import { mount } from '@vue/test-utils';
import Vuex from 'vuex';

import Notification from '@/components/notifications/Notification.vue';
import { stubFullNotification } from './stubs';

test('Notification renders the notification model', () => {
  const store = new Vuex.Store({
    modules: {
      activity: {
        namespaced: true,
        getters: {
          level: () => 'stub-activity-level',
        },
      },
    },
  });

  const notification = mount(Notification, {
    global: {
      plugins: [store],
    },
    props: stubFullNotification,
  });

  expect(notification.html()).toContain(stubFullNotification.token);
});

test('Notification renders a link if one is defined', () => {
  const store = new Vuex.Store({
    modules: {
      activity: {
        namespaced: true,
        getters: {
          level: () => 'stub-activity-level',
        },
      },
    },
  });

  const notification = mount(Notification, {
    global: {
      plugins: [store],
    },
    props: stubFullNotification,
  });

  expect(notification.find('a').attributes('href')).toEqual(stubFullNotification.link?.url.toString());
  expect(notification.find('a').attributes('target')).toEqual(stubFullNotification.link?.target);
  expect(notification.find('a').text()).toEqual(stubFullNotification.link?.text);
});
