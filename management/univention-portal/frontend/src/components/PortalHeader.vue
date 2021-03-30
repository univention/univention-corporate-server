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
  <header
    id="portal-header"
    class="portal-header"
  >
    <div
      ref="portalHeaderH1"
      class="portal-header__left"
      tabindex="0"
      @click="goHome"
    >
      <img
        class="portal-header__left-image"
        alt="Portal logo"
      >
      <h1 class="portal-header__portal-name">
        {{ $localized(portalName) }}
      </h1>
    </div>

    <div class="portal-header__tabs">
      <header-tab
        v-for="(item, index) in tabs"
        :key="index"
        :tab-index="index + 1"
        :tab-label="item.tabLabel"
        :is-active="activeTabIndex == index + 1"
        :logo="item.logo"
      />
    </div>

    <div class="portal-header__stretch" />

    <div
      v-if="editMode"
      class="portal-header__right"
    >
      <div>
        Edit mode
      </div>
      <header-button
        aria-label="Button for Edit mode"
        icon="settings"
      />
      <header-button
        aria-label="Stop edit mode"
        icon="x"
        @click="stopEditMode"
      />
    </div>
    <div
      v-else
      class="portal-header__right"
    >
      <header-button
        ref="searchButton"
        data-test="searchbutton"
        aria-label="Button for Searchbar"
        icon="search"
        @click="dismissBubble"
      />
      <header-button
        data-test="bellbutton"
        aria-label="Open notifications"
        icon="bell"
        @click="dismissBubble"
      />
      <header-button
        data-test="navigationbutton"
        aria-label="Button for navigation"
        icon="menu"
        @click="dismissNotification('menu')"
        @keydown.tab.exact.prevent="activeMenuButton ? dismissNotification('menu') : focusIntoSideNavIfOpen()"
      />
    </div>

    <notification-bubble>
      <template #bubble-standalone>
        <notification-bubble-slot bubble-container="standalone" />
      </template>
    </notification-bubble>
    <template v-if="activeButton === 'search'">
      <portal-search />
    </template>
  </header>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';

import HeaderButton from '@/components/navigation/HeaderButton.vue';
import HeaderTab from '@/components/navigation/HeaderTab.vue';
import NotificationBubble from '@/components/globals/NotificationBubble.vue';
import NotificationBubbleSlot from '@/components/globals/NotificationBubbleSlot.vue';
import PortalSearch from '@/components/search/PortalSearch.vue';

import notificationMixin from '@/mixins/notificationMixin.vue';

export default defineComponent({
  name: 'PortalHeader',
  components: {
    HeaderButton,
    HeaderTab,
    NotificationBubble,
    NotificationBubbleSlot,
    PortalSearch,
  },
  mixins: [
    notificationMixin,
  ],
  computed: {
    ...mapGetters({
      portalName: 'portalData/portalName',
      activeTabIndex: 'tabs/activeTabIndex',
      tabs: 'tabs/allTabs',
      editMode: 'portalData/editMode',
      activeButton: 'navigation/getActiveButton',
    }),
  },
  methods: {
    goHome(): void {
      this.$store.dispatch('tabs/setActiveTab', 0);
    },
    focusIntoSideNavIfOpen(): void {
      (document.querySelector('.portal-tile') as HTMLFormElement).focus();
    },
    stopEditMode(): void {
      this.$store.dispatch('portalData/setEditMode', false);
      this.$store.dispatch('navigation/setActiveButton', '');
    },
  },
});
</script>

<style lang="stylus">
.portal-header
  position: fixed
  top: 0
  left: 0
  right: 0
  z-index: $zindex-1
  background-color: var(--bgc-content-header)
  color: var(--font-color-contrast-high)
  height: var(--portal-header-height)
  display: flex
  padding: 0 calc(2 * var(--layout-spacing-unit))

  &__portal-name
    font-size: var(--font-size-2);

  &__left
    flex: 0 0 auto;
    display: flex;
    align-items: center;
    cursor: pointer;
    padding: 0px 10px
    border: 0.2rem solid rgba(0,0,0,0)

    &:focus
      border: 0.2rem solid var(--color-primary)
      outline: 0
    &-image
      display: none;

  &__tabs
    display: flex;
    flex: 1 1 auto;
    margin-left: calc(5 * var(--layout-spacing-unit));

  &__right
    display: flex;
    align-items: center;

  &__stretch
    flex: 1 1 auto;

  &__bubble-container
    width: 360px
</style>
