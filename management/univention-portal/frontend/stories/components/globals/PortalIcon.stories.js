/**
 * SPDX-License-Identifier: AGPL-3.0-only
 * SPDX-FileCopyrightText: 2023-2024 Univention GmbH
 */

import PortalIcon from '@/components/globals/PortalIcon';

export default {
  title: 'Components/Globals/PortalIcon',
  components: PortalIcon,
};

// Base Template
const Template = (args) => ({
  components: { PortalIcon },
  setup() {
    return {args};
  },
  template: '<portal-icon v-bind="args" />',
});

export const Basic = Template.bind({});
Basic.args = {
  icon: "feather",
};