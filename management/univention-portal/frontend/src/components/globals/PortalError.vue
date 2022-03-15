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
  <main class="portal-error">
    <h1 class="portal-error__title">
      {{ ERROR_MESSAGE }}
    </h1>
    <p class="portal-error__text">
      {{ ERROR_SUBTEXT }}
    </p>
  </main>
</template>
<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';
import _ from '@/jsHelper/translate';

export default defineComponent({
  name: 'Portalerror',
  props: {
    errorType: {
      type: Number,
      required: true,
    },
  },
  computed: {
    ...mapGetters({
      errorContentType: 'portalData/errorContentType',
    }),
    ERROR_MESSAGE(): string {
      if (this.errorType === 404) {
        return _('Page not found');
      }
      return _('Sorry.');
    },
    ERROR_SUBTEXT(): string {
      if (this.errorType === 404) {
        return _('This URL does not exist (anymore).');
      }
      return _('The portal is temporarily unavailable. If the problem persists, please contact your system administrator.');
    },
  },
  mounted() {
    this.$store.dispatch('activity/setMessage', `${this.ERROR_MESSAGE}. ${this.ERROR_SUBTEXT}`);
  },
});
</script>
<style lang="stylus">
.portal-error
  position: relative
  display: flex
  flex-direction: column
  margin-left: calc(2 * var(--layout-spacing-unit) + var(--layout-spacing-unit) + 0.2rem)

  @media $mqSmartphone
    margin-left: 1em

  &__title
    margin-bottom: 0
</style>
