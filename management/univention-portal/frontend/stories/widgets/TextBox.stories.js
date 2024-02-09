/**
 * SPDX-License-Identifier: AGPL-3.0-only
 * SPDX-FileCopyrightText: 2023-2024 Univention GmbH
 */

import MyForm from '../../src/components/forms/Form.vue';

export default {
  title: 'Widgets/TextBox',
  component: MyForm,
};

const modalStyle = `
padding: calc(2 * var(--layout-spacing-unit)) calc(2 * var(--layout-spacing-unit));
background: var(--bgc-content-container);
border-radius: var(--border-radius-container);
max-width: calc(50 * var(--layout-spacing-unit));
box-shadow: var(--box-shadow);`;

const Template = (args) => ({
  components: { MyForm },
  setup() {
    return { args };
  },
  template: `<div style="${modalStyle}"><my-form v-model="args.modelValue" :widgets="args.widgets"></my-Form></div>`,
});

const textBoxProp = [{
  type: 'TextBox',
  name: 'username',
  label: 'Username',
  invalidMessage: '',
  required: true,
}];


export const Default = Template.bind({});
Default.args = {
  modelValue: {username: ''},
  widgets: textBoxProp,
};
