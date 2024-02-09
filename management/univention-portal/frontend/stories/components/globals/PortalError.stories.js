/**
 * SPDX-License-Identifier: AGPL-3.0-only
 * SPDX-FileCopyrightText: 2023-2024 Univention GmbH
 */

import PortalError from '@/components/globals/PortalError';

export default {
  title: 'Components/Globals/PortalError',
  components: PortalError,
};

// Base Template
const Template = (args) => ({
  components: { PortalError },
  setup() {
    return {args};
  },
  template: '<portal-error v-bind="args" />',
});

export const General = Template.bind({});
General.args = {
  errorType: null
};

export const Error404 = Template.bind({});
Error404.args = {
  errorType: 404
};