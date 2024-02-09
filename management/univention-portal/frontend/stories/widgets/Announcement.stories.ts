/**
 * SPDX-License-Identifier: AGPL-3.0-only
 * SPDX-FileCopyrightText: 2023-2024 Univention GmbH
 */

import { Meta, StoryFn } from '@storybook/vue3';

import Announcement from '../../src/components/widgets/Announcement.vue';

export default {
  title: 'Widgets/Announcement',
  components: Announcement,
  parameters: {
    layout: 'centered',
  },
  argTypes: {
    severity: {
      control: {
        type: 'select',
        options: ['info', 'danger', 'success', 'warn'],
      },
    },
  },
} as Meta<typeof Announcement>;

// Base Template
const Template: StoryFn<typeof Announcement> = (args) => ({
  components: { Announcement },
  setup() {
    return { args };
  },
  template: `
  <div>
    <announcement v-bind='args' />
  </div>`
});

export const Basic = Template.bind({});
Basic.args = {
  severity: 'success',
  title:{
    'en': 'My Title',
  },
  message:{
    'en': 'My Message',
  },
  name: 'unique_announcement',
  sticky: false
};
