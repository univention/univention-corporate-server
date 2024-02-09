/**
 * SPDX-License-Identifier: AGPL-3.0-only
 * SPDX-FileCopyrightText: 2023-2024 Univention GmbH
 */

import { Meta, StoryFn } from '@storybook/vue3';

import ComplexInput from '@/components/widgets/ComplexInput.vue';

export default {
  title: 'Widgets/ComplexInput',
  components: ComplexInput,
  parameters: {
    layout: 'centered',
  },
} as Meta<typeof ComplexInput>;

// Base Template
const Template: StoryFn<typeof ComplexInput> = (args) => ({
  components: { ComplexInput },
  setup() {
    return { args };
  },
  template: '<ComplexInput v-bind="args"/>',
});

export const Basic = Template.bind({});
Basic.args = {
  type: 'ComplexInput',
  name: 'complexInput',
  label: 'complexInput',
  // direction: 'vertical',
  required: false,
  readonly: false,
  modelValue: ['TextBox', '2022-12-12', '11:20', 'DE'],
  subtypes: [
    {
      type: 'TextBox',
      name: 'text',
      label: 'TextBox',
    },
    {
      type: 'DateBox',
      name: 'date',
      label: 'DateBox',
    },
    {
      type: 'TimeBox',
      name: 'time',
      label: 'TimeBox',
    },
    {
      type: 'ComboBox',
      name: 'timeZone',
      label: 'ComboBox',
      options: [{
        id: 'DE',
        label: 'Germany',
      }],
    },
  ],
};
