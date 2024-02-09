/**
 * SPDX-License-Identifier: AGPL-3.0-only
 * SPDX-FileCopyrightText: 2023-2024 Univention GmbH
 */

import { Meta, StoryFn } from '@storybook/vue3';

import SuggestionBox from '@/components/widgets/SuggestionBox.vue';

export default {
  title: 'Widgets/SuggestionBox',
  components: SuggestionBox,
} as Meta<typeof SuggestionBox>;

// Base Template
const Template: StoryFn<typeof SuggestionBox> = (args) => ({
  components: { SuggestionBox },
  setup() {
    return { args };
  },
  template: '<div><SuggestionBox v-bind="args" /></div>',
});

export const Basic = Template.bind({});
Basic.args = {
  modelValue: '',
  suggestedOptions: [
    'Apple', 'Banana', 'Cherry', 'Duran', 'Elderberry',
  ] };
