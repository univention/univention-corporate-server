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
  <tabindex-element
    id="portalTitle"
    :active-at="['portal']"
    :aria-label="SHOW_PORTAL"
    tag="div"
    class="portal-title"
    role="button"
    @click="goHome"
    @keydown.enter="goHome"
  >
    <img
      v-if="portalLogo"
      :src="portalLogo"
      class="portal-title__image"
      alt=""
    >
    <div
      v-else
      class="portal-title__portal-home-icon"
    >
      <PortalIcon icon="home" />
    </div>

    <h1
      v-if="portalNameString"
      class="portal-title__portal-name sr-only-mobile"
    >
      {{ portalNameString }}
    </h1>
  </tabindex-element>
</template>
<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';
import _ from '@/jsHelper/translate';

import TabindexElement from '@/components/activity/TabindexElement.vue';
import PortalIcon from '@/components/globals/PortalIcon.vue';

export default defineComponent({
  name: 'PortalTitle',
  components: {
    PortalIcon,
    TabindexElement,
  },
  computed: {
    ...mapGetters({
      portalLogo: 'portalData/portalLogo',
      portalName: 'portalData/portalName',
      savedScrollPosition: 'tabs/savedScrollPosition',
      activeButton: 'navigation/getActiveButton',
    }),
    SHOW_PORTAL(): string {
      return _('Show portal');
    },
    portalNameString(): string {
      return this.$localized(this.portalName);
    },
  },
  methods: {
    goHome(): void {
      this.$store.dispatch('tabs/setActiveTab', 0);
      setTimeout(() => {
        window.scrollTo(0, this.savedScrollPosition);
      }, 10);
      this.$store.dispatch('navigation/setActiveButton', '');
    },
  },
});

</script>
<style lang="stylus">
.portal-title
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 0px 10px
  border: 0.2rem solid rgba(0,0,0,0)

  &:focus
    border: 0.2rem solid var(--color-focus)
    outline: 0

  &__image
    height: 100%
    width: calc(var(--portal-header-height) * var(--portal-header-icon-scale))

  &__portal-home-icon
    display: none
    @media $mqSmartphone
      display: flex
      align-content: center

      svg
        width: calc(3* var(--layout-spacing-unit))
        height: @width

  &__portal-name
    font-size: var(--font-size-2);
    white-space: nowrap
    padding-left: var(--layout-spacing-unit)
</style>
