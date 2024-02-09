/**
 * SPDX-License-Identifier: AGPL-3.0-only
 * SPDX-FileCopyrightText: 2023-2024 Univention GmbH
 */

import { Meta, StoryFn } from '@storybook/vue3';

import ProgressBar from '@/components/widgets/ProgressBar.vue';

export default {
  title: 'Widgets/ProgressBar',
  components: ProgressBar,
} as Meta<typeof ProgressBar>;

// Base Template
const Template: StoryFn<typeof ProgressBar> = (args) => ({
  components: { ProgressBar },
  setup() {
    return { args };
  },
  template: '<div><ProgressBar v-bind="args" /></div>',
});

export const Basic = Template.bind({});
Basic.args = { title: 'My ProgressBar', percentage: 50, message: 'Installing packages x' };
