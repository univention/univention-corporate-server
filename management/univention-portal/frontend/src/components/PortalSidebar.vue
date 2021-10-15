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
      :is-active="activeNotificationButton || activeMenuButton || activeEditModeButton"
      @backgroundClick="closeSidebar"
    >
      <transition
        name="slide"
        appear
      >
        <flyout-wrapper
          v-if="activeNotificationButton"
          :is-visible="activeNotificationButton"
          class="portal-sidebar__flyout"
        >
          <!-- Side notifications -->
          <notifications :is-in-notification-bar="true" />
        </flyout-wrapper>
      </transition>

      <transition
        name="slide"
        appear
      >
        <flyout-wrapper
          v-if="activeMenuButton"
          :is-visible="activeMenuButton"
          class="portal-sidebar__flyout"
        >
          <!-- Side navigation -->
          <side-navigation :links="menuItems" />
        </flyout-wrapper>
      </transition>

      <transition
        name="slide"
        appear
      >
        <flyout-wrapper
          :is-visible="activeEditModeButton"
          class="portal-sidebar__flyout"
        >
          <!-- Edit mode -->
          <edit-mode-side-navigation v-if="activeEditModeButton" />
        </flyout-wrapper>
      </transition>
    </modal-wrapper>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';

import FlyoutWrapper from '@/components/navigation/FlyoutWrapper.vue';
import ModalWrapper from '@/components/modal/ModalWrapper.vue';
import Notifications from '@/components/notifications/Notifications.vue';
import SideNavigation from '@/components/navigation/SideNavigation.vue';
import EditModeSideNavigation from '@/components/navigation/EditModeSideNavigation.vue';

export default defineComponent({
  name: 'PortalSidebar',
  components: {
    FlyoutWrapper,
    ModalWrapper,
    Notifications,
    SideNavigation,
    EditModeSideNavigation,
  },
  computed: {
    ...mapGetters({
      portalName: 'portalData/portalName',
      activeButton: 'navigation/getActiveButton',
      activeTabIndex: 'tabs/activeTabIndex',
      menuItems: 'menu/getMenu',
      tabs: 'tabs/allTabs',
    }),
    activeNotificationButton(): boolean {
      return this.activeButton === 'bell';
    },
    activeMenuButton(): boolean {
      return this.activeButton === 'menu';
    },
    activeEditModeButton(): boolean {
      return this.activeButton === 'settings';
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
    font-weight: normal

.slide-enter-active,
.slide-leave-active {
  transition: transform 0.5s ease;
}

.slide-enter-from,
.slide-leave-to {
  transform: translateX(22rem)
}
</style>
