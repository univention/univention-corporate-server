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
  <div class="portal-sidebar">
    <modal-wrapper
      :is-active="activeNotificationButton || activeMenuButton"
      @backgroundClick="closeSidebar"
    >
      <flyout-wrapper
        :is-visible="activeNotificationButton || activeMenuButton"
        class="portal-sidebar__flyout"
      >
        <!-- Side notifications -->
        <div v-if="activeNotificationButton">
          <div class="portal-sidebar__title">
            <translate i18n-key="NOTIFICATIONS" />
          </div>
          <notification-bubble class="portal-sidebar__bubble">
            <template #bubble-embedded>
              <notification-bubble-slot bubble-container="embedded" />
            </template>
          </notification-bubble>
        </div>
        <!-- Side navigation -->
        <side-navigation v-if="activeMenuButton" />
      </flyout-wrapper>
    </modal-wrapper>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';

import FlyoutWrapper from '@/components/navigation/FlyoutWrapper.vue';
import ModalWrapper from '@/components/globals/ModalWrapper.vue';
import NotificationBubble from '@/components/globals/NotificationBubble.vue';
import NotificationBubbleSlot from '@/components/globals/NotificationBubbleSlot.vue';
import SideNavigation from '@/components/navigation/SideNavigation.vue';

import Translate from '@/i18n/Translate.vue';

export default defineComponent({
  name: 'PortalSidebar',
  components: {
    FlyoutWrapper,
    ModalWrapper,
    NotificationBubble,
    NotificationBubbleSlot,
    SideNavigation,
    Translate,
  },
  computed: {
    ...mapGetters({
      portalName: 'portalData/portalName',
      activeButton: 'navigation/getActiveButton',
      activeTabIndex: 'tabs/activeTabIndex',
      tabs: 'tabs/allTabs',
    }),
    activeNotificationButton(): boolean {
      return this.activeButton === 'bell';
    },
    activeMenuButton(): boolean {
      return this.activeButton === 'menu';
    },
  },
  methods: {
    closeSidebar(): void {
      this.$store.dispatch('navigation/setActiveButton', '');
    },
  },
});
</script>

<style lang="stylus">
.portal-sidebar

  &__title
    margin: calc(2 * var(--layout-spacing-unit)) 0
    margin-left: calc(2.5 * var(--layout-spacing-unit))
    font-size: 20px

  &__flyout
    width: 22rem
    max-width: 22rem
    min-height: 100vh

  &__bubble
    padding: 0 20px
</style>
