<!--
  Copyright 2021-2022 Univention GmbH

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
  <div
    v-if="displayCondition"
    class="input-error-message"
  >
    <portal-icon
      icon="alert-circle"
      class="input-error-message__icon"
    />
    <span>
      {{ errorMessage }}
    </span>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';

import PortalIcon from '@/components/globals/PortalIcon.vue';

export default defineComponent({
  name: 'InputErrorMessage',
  components: {
    PortalIcon,
  },
  props: {
    errorMessage: {
      type: String,
      required: true,
    },
    displayCondition: {
      type: Boolean,
      required: true,
    },
  },
});
</script>

<style lang="stylus">
.input-error-message
    display: flex
    align-items: center
    color: var(--font-color-error)
    margin-bottom: var(--layout-spacing-unit)

    &__icon
        flex: 0 0 auto
        margin-right: var(--layout-spacing-unit-small)
        color: var(--font-color-error)
</style>
