/**
 * SPDX-License-Identifier: AGPL-3.0-only
 * SPDX-FileCopyrightText: 2023-2024 Univention GmbH
 */

import { Meta, StoryFn } from '@storybook/vue3';

import MailBox from '../../src/components/widgets/MailBox.vue';

export default {
  title: 'Widgets/MailBox',
  components: MailBox,
  parameters: {
    layout: 'centered',
  },
} as Meta<typeof MailBox>;

// Base Template
const Template: StoryFn<typeof MailBox> = (args) => ({
  components: { MailBox },
  setup() {
    return { args };
  },
  template: '<div style="width: 500px; padding: 1rem;"><MailBox v-bind="args" /></div>',
});

export const Basic = Template.bind({});
Basic.args = {
  name: 'MailBox',
  label: 'My MailBox',
  modelValue: '',
  domainList: [
    'google.com', 'example.de',
  ],
};
