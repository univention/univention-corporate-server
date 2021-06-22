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
  <div class="portal">
    <portal-background />
    <portal-header />

    <region
      v-show="!activeTabIndex"
      id="portalCategories"
      role="main"
      class="portal-categories"
    >
      <div
        aria-live="assertive"
        aria-atomic="true"
      >
        <h2 v-if="hasEmptySearchResults">
          <translate i18n-key="NO_RESULTS" />
        </h2>
      </div>

      <template v-if="categories">
        <portal-category
          v-for="category in categories"
          :key="category.id"
          :title="category.title"
          :dn="category.dn"
          :virtual="category.virtual"
          :tiles="category.tiles"
        />
      </template>

      <h2
        v-if="editMode"
        class="portal-categories__title"
      >
        <icon-button
          icon="plus"
          class="portal-categories__add-button icon-button--admin"
          :aria-label-prop="ariaLabelAddNewTile"
          @click="addCategory"
        />
        <translate i18n-key="ADD_CATEGORY" />
      </h2>
    </region>

    <div
      v-show="activeTabIndex"
      class="portal-iframes"
    >
      <portal-iframe
        v-for="(item, index) in tabs"
        :key="index"
        :link="item.iframeLink"
        :is-active="activeTabIndex == index + 1"
      />
    </div>

    <notifications :only-visible="true" />

    <portal-tool-tip
      v-if="tooltip"
      v-bind="tooltip"
    />

    <portal-sidebar />
    <portal-modal :is-active="false" />
    <loading-overlay />
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';

import IconButton from '@/components/globals/IconButton.vue';
import Region from '@/components/activity/Region.vue';
import ModalWrapper from '@/components/globals/ModalWrapper.vue';
import Notifications from 'components/notifications/Notifications.vue';
import PortalBackground from '@/components/PortalBackground.vue';
import PortalCategory from 'components/PortalCategory.vue';
import PortalHeader from '@/components/PortalHeader.vue';
import PortalIframe from 'components/PortalIframe.vue';
import PortalModal from 'components/PortalModal.vue';
import PortalSidebar from '@/components/PortalSidebar.vue';
import PortalToolTip from 'components/PortalToolTip.vue';
import LoadingOverlay from '@/components/globals/LoadingOverlay.vue';

import Translate from '@/i18n/Translate.vue';

import { Category } from '@/store/modules/portalData/portalData.models';
import createCategories from '@/jsHelper/createCategories';

export default defineComponent({
  name: 'Portal',
  components: {
    IconButton,
    LoadingOverlay,
    ModalWrapper,
    Notifications,
    PortalBackground,
    PortalCategory,
    PortalHeader,
    PortalIframe,
    PortalModal,
    PortalSidebar,
    PortalToolTip,
    Region,
    Translate,
  },
  computed: {
    ...mapGetters({
      portalContent: 'portalData/portalContent',
      portalEntries: 'portalData/portalEntries',
      portalFolders: 'portalData/portalFolders',
      portalCategories: 'portalData/portalCategories',
      portalDefaultLinkTarget: 'portalData/portalDefaultLinkTarget',
      tabs: 'tabs/allTabs',
      activeTabIndex: 'tabs/activeTabIndex',
      editMode: 'portalData/editMode',
      tooltip: 'tooltip/tooltip',
      hasEmptySearchResults: 'search/hasEmptySearchResults',
      metaData: 'metaData/getMeta',
    }),
    categories(): Category[] {
      return createCategories(this.portalContent, this.portalCategories, this.portalEntries, this.portalFolders, this.portalDefaultLinkTarget, this.editMode);
    },
    ariaLabelAddNewTile(): string {
      return this.$translateLabel('ADD_NEW_CATEGORY');
    },
  },
  methods: {
    addCategory() {
      this.$store.dispatch('modal/setAndShowModal', {
        name: 'CategoryAddModal',
      });
      this.$store.dispatch('activity/setRegion', 'category-add-modal');
    },
  },
});
</script>

<style lang="stylus">
.portal-categories
  position: relative;
  padding: calc(4 * var(--layout-spacing-unit)) calc(6 * var(--layout-spacing-unit));

  @media $mqSmartphone
    padding: calc(4 * var(--layout-spacing-unit)) calc(4 * var(--layout-spacing-unit));

  &__add
    margin-top: -50px;

  &__add-button
    vertical-align: top

    svg
      vertical-align: top

  &__title
    display: inline-block
    margin-top: 0
    margin-bottom: calc(6 * var(--layout-spacing-unit))

  &__menu-wrapper
    width: 100%
    display: flex;
    flex-direction: row;
    flex-wrap: nowrap;
    justify-content: flex-start;
    align-content: flex-start;
    align-items: flex-start;
    position: absolute

  &__menu-container
    position: relative
    order: 0;
    flex: 0 1 auto;
    align-self: auto;

  &__icon
    position: absolute
    right: 15px
    margin-top: 2px

.portal-iframes
  position: fixed
  top: var(--portal-header-height)
  border: 0px solid var(--portal-tab-background)
  border-top-width: var(--layout-height-header-separator)
  right: 0
  bottom: 0
  left: 0

</style>
