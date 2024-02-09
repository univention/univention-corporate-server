/**
 * SPDX-License-Identifier: AGPL-3.0-only
 * SPDX-FileCopyrightText: 2023-2024 Univention GmbH
 */

import LoadingOverlay from '@/components/globals/LoadingOverlay';

export default {
  title: 'Components/Globals/LoadingOverlay',
  components: LoadingOverlay,
};

// Base Template
const Template = () => ({
  components: { LoadingOverlay },
  setup() {
    return {};
  },
  template: '<loading-overlay />',
});

export const Basic = Template.bind({});
