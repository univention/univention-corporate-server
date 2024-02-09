/**
 * SPDX-License-Identifier: AGPL-3.0-only
 * SPDX-FileCopyrightText: 2023-2024 Univention GmbH
 */

import { Meta, StoryFn } from '@storybook/vue3';

import MyForm from '@/components/forms/Form.vue';
import { validateAll } from '../../src/jsHelper/forms';

export default {
  title: 'Widgets/All Widgets',
  components: MyForm,
  parameters: {
    layout: 'centered',
  },
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
  template: `
    <div>
      <MyForm v-model="formValues" :widgets="formWidgets" />
      <button @click="validate" style="margin: 1rem 0">validate</button>
    </div>`,
  methods: {
    // handleUpdate(newValue) {
    //   setTimeout(() => {
    //     updateArgs({ ...args, ...{ formValues: newValue } });
    //   }, 1000);
    // },
    validate() {
      validateAll(this.formWidgets, this.formValues);
    },
  },
});

function validator(_widget: any, value: string): string {
  const regex = new RegExp('^[0-9]*$');
  if (!regex.test(value)) {
    return ('Internal name must not contain anything other than digits, letters or dots, must be at least 2 characters long, and start and end with a digit or letter!');
  }
  return '';
}

export const Basic = Template.bind({});
Basic.args = {
  formValues: {
    password: '',
    text: '',
    complexInput: ['', '2022-12-12', '11:20', 'DE'],
    multiInput: [],
  },
  formWidgets: [
    {
      type: 'PasswordBox',
      name: 'password',
      label: 'PasswordBox',
    },
    {
      type: 'TextBox',
      name: 'text',
      label: 'TextBox',
      validators: [validator],
    },
    {
      type: 'ComplexInput',
      name: 'complexInput',
      label: 'ComplexInput',

      subtypes: [
        {
          type: 'TextBox',
          name: 'text',
          label: 'TextBox',
          validators: [validator],
        },
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
