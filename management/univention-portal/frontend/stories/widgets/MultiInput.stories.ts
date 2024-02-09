/**
 * SPDX-License-Identifier: AGPL-3.0-only
 * SPDX-FileCopyrightText: 2023-2024 Univention GmbH
 */

import { Meta, StoryFn } from '@storybook/vue3';
import MyForm from '@/components/forms/Form.vue';

export default {
  title: 'Widgets/MultiInput',
  components: MyForm,
} as Meta<typeof MyForm>;

// Base Template
const Template: StoryFn<typeof MyForm> = (args, { updateArgs }) => ({
  components: { MyForm },
  setup() {
    return { args };
  },
  data() {
    return {
      formValues: args.formValues,
      formWidgets: args.formWidgets,
    };
  },
  template: '<MyForm v-model="formValues"  :widgets="formWidgets" />',
});

export const Basic = Template.bind({});
Basic.args = {
  formValues: {
    multiInput: [''],
  },
  formWidgets: [
    {
      type: 'MultiInput',
      name: 'multiInput',
      label: 'MultiInput',
      extraLabel: 'MultiInput',

      subtypes: [
        {
          type: 'DateBox',
          name: 'date',
          label: 'date',
        },
        {
          type: 'TimeBox',
          name: 'time',
          label: 'time',
        },
        {
          type: 'ComboBox',
          name: 'timeZone',
          label: 'timeZone',
          options: [{
            id: 'DE',
            label: 'Germany',
          }],
        },
      ],
    },
  ],
};
