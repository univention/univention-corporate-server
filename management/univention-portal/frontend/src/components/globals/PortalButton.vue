<!--
Copyright 2021 Univention GmbH

https://www.univention.de/

All rights reserved.

The source code of this program is made available
under the terms of the GNU Affero General Public License version 3
(GNU AGPL V3) as published by the Free Software Foundation.

Binary versions of this program provided by Univention to you as
well as other copyrighted, protected or trademarked materials like
Logos, graphics, fonts, specific documentations and configurations,
cryptographic keys etc. are subject to a license agreement between
you and Univention and not subject to the GNU AGPL V3.

In the case you use this program under the terms of the GNU AGPL V3,
the program is provided in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public
License with the Debian GNU/Linux or Univention distribution in file
/usr/share/common-licenses/AGPL-3; if not, see
<https://www.gnu.org/licenses/>.
-->
<template>
  <div class="portal-button">
    <!-- button component -->
    <span
      role="button"
      aria-labelledby="DO_WE_USE_THAT"
      tabindex="0"
      style="user-select: none;"
    >
      <portal-icon
        v-if="iconBefore"
        :class="iconBeforeClass || iconBeforeClass"
        :icon="iconBefore"
        icon-width="2rem"
      />
      <span>
        {{ BUTTON_LABEL }}
      </span>
      <portal-icon
        v-if="iconAfter"
        :class="iconAfterClass || iconAfterClass"
        :icon="iconAfter"
        icon-width="2rem"
      />
    </span>
    <input
      name="accept"
      type="button"
      value=""
      class="portal__off-screen"
      tabindex="-1"
      aria-hidden="true"
    >
    <!-- button component -->
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import _ from '@/jsHelper/translate';

import PortalIcon from '@/components/globals/PortalIcon.vue';

export default defineComponent({
  name: 'PortalButton',
  components: {
    PortalIcon,
  },
  props: {
    buttonLabel: {
      type: String,
      default: _('Submit'),
    },
    iconBefore: {
      type: String,
      default: '',
    },
    iconBeforeClass: {
      type: String,
      default: '',
    },
    iconAfter: {
      type: String,
      default: '',
    },
    iconAfterClass: {
      type: String,
      default: '',
    },
  },
  computed: {
    BUTTON_LABEL(): string {
      _('%(key1)s', { key1: buttonLabel });
    },
  },
});
</script>

<style lang="stylus">
.portal-button
  user-select: none;
</style>
