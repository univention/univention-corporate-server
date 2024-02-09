/**
 * SPDX-License-Identifier: AGPL-3.0-only
 * SPDX-FileCopyrightText: 2023-2024 Univention GmbH
 */

import IconButton from '@/components/globals/IconButton';

export default {
  title: 'Components/Globals/IconButton',
  components: IconButton,
};

const Template = (args) => ({
  components: { IconButton },
  setup() {
    return {args};
  },
  template: '<icon-button v-bind="args"></icon-button>',
});

export const Default = Template.bind({});
Default.args = {
  icon: "search",
  ariaLabelProp: "Search"
};

export const Focused = Template.bind({});
Focused.args = {
  ...Default.args,
};
Focused.parameters = {pseudo: { focus: true }};

export const ButtonStyle = Template.bind({});
ButtonStyle.args = {
  ...Default.args,
  hasButtonStyle: true,
};
export const ButtonStyleFocused = Template.bind({});
ButtonStyleFocused.args = {
  ...Default.args,
  hasButtonStyle: true,
};
ButtonStyleFocused.parameters = {pseudo: { focus: true }};
