/**
 * SPDX-License-Identifier: AGPL-3.0-only
 * SPDX-FileCopyrightText: 2023-2024 Univention GmbH
 */

import PortalHeader from '@/components/PortalHeader.vue';
import { store } from '@/store/';

store.dispatch('portalData/setPortalName', {de_DE: 'Portal', en_US: 'Portal'});

export default {
  title: 'Components/PortalHeader',
  component: PortalHeader,
};

const Template = () => ({
  components: { PortalHeader },
  setup() {
    return {};
  },
  template: `<portal-header></portal-header>`,
});


export const Default = Template.bind({});
