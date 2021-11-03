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
  <region
    id="portal-header"
    role="banner"
    :class="{ 'portal-header__tabs-overflow': tabsOverflow }"
    class="portal-header"
  >
    <portal-title />

    <div
      ref="tabs"
      class="portal-header__tabs"
      data-test="header-tabs"
    >
      <header-tab
        v-for="(item, index) in tabs"
        :key="index"
        :idx="index + 1"
        :tab-label="item.tabLabel"
        :is-active="activeTabIndex == index + 1"
        :background-color="item.backgroundColor"
        :logo="item.logo"
        :hidden="tabsOverflow"
      />
    </div>

    <div
      v-if="editMode"
      class="portal-header__edit-mode-label"
    >
      {{ EDIT_MODE }}
      <header-button
        :aria-label-prop="STOP_EDIT_PORTAL"
        icon="x"
        @click="stopEditMode"
      />
    </div>
    <div
      v-if="editMode"
      class="portal-header__right"
    >
      <header-button
        data-test="bellbutton"
        :aria-label-prop="NOTIFICATIONS"
        icon="bell"
        :counter="numNotifications"
        @keydown.esc="closeNotificationsSidebar"
        @keydown.right="closeNotificationsSidebar"
        @keydown.left="closeNotificationsSidebar"
      />
      <header-button
        data-test="settingsbutton"
        :aria-label-prop="OPEN_EDIT_SIDEBAR"
        icon="settings"
      />
    </div>
    <div
      v-else
      class="portal-header__right"
    >
      <header-button
        v-if="showTabButton"
        ref="tabButton"
        data-test="tabbutton"
        :aria-label-prop="TABS"
        icon="copy"
        :counter="numTabs"
        class="portal-header__tab-button"
      />
      <header-button
        ref="searchButton"
        data-test="searchbutton"
        :aria-label-prop="SEARCH"
        icon="search"
      />
      <header-button
        data-test="bellbutton"
        :aria-label-prop="NOTIFICATIONS"
        icon="bell"
        :counter="numNotifications"
        @keydown.esc="closeNotificationsSidebar"
        @keydown.right="closeNotificationsSidebar"
        @keydown.left="closeNotificationsSidebar"
      />
      <header-button
        :aria-label-prop="MENU"
        data-test="navigationbutton"
        icon="menu"
      />
    </div>

    <template v-if="activeButton === 'search'">
      <portal-search />
    </template>
  </region>
  <choose-tabs
    v-if="activeButton === 'copy'"
  />
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';
import _ from '@/jsHelper/translate';

import Region from '@/components/activity/Region.vue';
import TabindexElement from '@/components/activity/TabindexElement.vue';
import HeaderButton from '@/components/navigation/HeaderButton.vue';
import HeaderTab from '@/components/navigation/HeaderTab.vue';
import PortalSearch from '@/components/search/PortalSearch.vue';
import ChooseTabs from '@/components/ChooseTabs.vue';
import PortalIcon from '@/components/globals/PortalIcon.vue';
import PortalTitle from '@/components/header/PortalTitle.vue';

interface PortalHeaderData {
  tabsOverflow: boolean;
}

export default defineComponent({
  name: 'PortalHeader',
  components: {
    HeaderButton,
    HeaderTab,
    PortalSearch,
    ChooseTabs,
    PortalIcon,
    Region,
    TabindexElement,
    PortalTitle,
  },
  data(): PortalHeaderData {
    return {
      tabsOverflow: false,
    };
  },
  computed: {
    ...mapGetters({
      portalLogo: 'portalData/portalLogo',
      portalName: 'portalData/portalName',
      activeTabIndex: 'tabs/activeTabIndex',
      tabs: 'tabs/allTabs',
      savedScrollPosition: 'tabs/savedScrollPosition',
      numTabs: 'tabs/numTabs',
      editMode: 'portalData/editMode',
      activeButton: 'navigation/getActiveButton',
      numNotifications: 'notifications/numNotifications',
    }),
    showTabButton(): boolean {
      return this.numTabs > 0 && this.tabsOverflow;
    },
    SHOW_PORTAL(): string {
      return _('Show portal');
    },
    EDIT_MODE(): string {
      return _('Edit mode');
    },
    OPEN_EDIT_SIDEBAR(): string {
      return _('Open edit sidebar');
    },
    STOP_EDIT_PORTAL(): string {
      return _('Stop edit portal');
    },
    TABS(): string {
      return _('Tabs');
    },
    SEARCH(): string {
      return _('search');
    },
    NOTIFICATIONS(): string {
      return _('Notifications');
    },
    MENU(): string {
      return _('Menu');
    },
  },
  watch: {
    numTabs(): void {
      this.$nextTick(() => {
        this.updateOverflow();
      });
    },
  },
  mounted() {
    this.$nextTick(() => {
      window.addEventListener('resize', this.updateOverflow);
    });
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.updateOverflow);
  },
  methods: {
    updateOverflow() {
      const tabs = this.$refs.tabs as HTMLElement;
      if (tabs === null) {
        return;
      }
      this.tabsOverflow = tabs.scrollWidth > tabs.clientWidth;
    },
    closeNotificationsSidebar(): void {
      this.$store.dispatch('navigation/closeNotificationsSidebar');
    },
    chooseTab(): void {
      this.$store.dispatch('modal/setAndShowModal', {
        name: 'ChooseTabs',
      });
    },
    goHome(): void {
      this.$store.dispatch('tabs/setActiveTab', 0);
      setTimeout(() => {
        window.scrollTo(0, this.savedScrollPosition);
      }, 10);
      this.$store.dispatch('navigation/setActiveButton', '');
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
  z-index: $zindex-3
  background-color: var(--bgc-content-header)
  color: var(--font-color-contrast-high)
  height: var(--portal-header-height)
  display: flex
  padding: 0 calc(2 * var(--layout-spacing-unit))

  &__tabs
    display: flex;
    flex: 1 1 auto;
    margin-left: calc(5 * var(--layout-spacing-unit));
    width: 100%;
    overflow: hidden
    align-items: center

  &__right
    margin-left: auto
    display: flex;
    align-items: center;

  &__edit-mode-label
    white-space: nowrap
    position: absolute
    top: var(--layout-height-header)
    display: flex
    min-width: 150px
    right: calc(50% - 75px)
    background-color: var(--bgc-content-header)
    align-items: center
    justify-content: center
    padding-left: calc(var(--button-size) / 2)

    @media $mqSmartphone
      top: calc(var(--layout-height-header) - 62%)

#header-button-copy
    display: none

.portal-header__tabs-overflow
  .portal-header
    &__tabs
      visibility: hidden
  #header-button-copy
      display: flex
</style>
