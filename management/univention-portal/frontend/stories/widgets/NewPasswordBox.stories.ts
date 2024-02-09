/**
 * SPDX-License-Identifier: AGPL-3.0-only
 * SPDX-FileCopyrightText: 2023-2024 Univention GmbH
 */

import { Meta, StoryFn } from '@storybook/vue3';

import NewPasswordBox from '../../src/components/widgets/NewPasswordBox.vue';

export default {
  title: 'Widgets/NewPasswordBox',
  components: NewPasswordBox,
  parameters: {
    layout: 'centered',
  },
} as Meta<typeof NewPasswordBox>;

// Base Template
const Template: StoryFn<typeof NewPasswordBox> = (args) => ({
  components: { NewPasswordBox },
  setup() {
    return { args };
  },
  template: `
  <div>
    <new-password-box v-bind='args' />
  </div>`
});

export const Basic = Template.bind({});
Basic.args = {
  name: "my name",
  modelValue: {"": ""},
  invalidMessage: {"": ""},
  forAttrOfLabel: "forAttrOfLabel",
  invalidMessageId: "invalidMessageId",
  disabled: false,
  tabindex: 0,
  required: true,
  canShowPassword: true,
};