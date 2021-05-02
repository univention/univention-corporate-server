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

    <main
      v-show="!activeTabIndex"
      id="portalCategories"
      class="portal-categories"
    >
      <template v-if="categories">
        <portal-category
          v-for="category in categories"
          :key="category.id"
          :title="category.title"
          :dn="category.dn"
          :tiles="category.tiles"
        />
      </template>

      <h2
        v-if="editMode"
        class="portal-categories__title"
        @click.prevent="addCategory()"
      >
        <icon-button
          icon="plus"
          class="portal-categories__add-button"
        />
        <translate i18n-key="ADD_CATEGORY" />
      </h2>
    </main>

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

    <portal-tool-tip
      v-if="tooltip"
      v-bind="tooltip"
    />

    <portal-sidebar />
    <portal-modal :is-active="false" />
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';

import IconButton from '@/components/globals/IconButton.vue';
import ModalWrapper from '@/components/globals/ModalWrapper.vue';
import PortalBackground from '@/components/PortalBackground.vue';
import PortalCategory from 'components/PortalCategory.vue';
import PortalHeader from '@/components/PortalHeader.vue';
import PortalIframe from 'components/PortalIframe.vue';
import PortalModal from 'components/PortalModal.vue';
import PortalSidebar from '@/components/PortalSidebar.vue';
import PortalToolTip from 'components/PortalToolTip.vue';

import notificationMixin from '@/mixins/notificationMixin.vue';
import Translate from '@/i18n/Translate.vue';

import { Category } from '@/store/modules/portalData/portalData.models';
import createCategories from '@/jsHelper/createCategories';

export default defineComponent({
  name: 'Portal',
  components: {
    IconButton,
    ModalWrapper,
    PortalBackground,
    PortalCategory,
    PortalHeader,
    PortalIframe,
    PortalModal,
    PortalSidebar,
    PortalToolTip,
    Translate,
  },
  mixins: [notificationMixin],
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
    }),
    categories(): Category[] {
      return createCategories(this.portalContent, this.portalCategories, this.portalEntries, this.portalFolders, this.portalDefaultLinkTarget, this.editMode);
    },
    setModalContent() {
      let ret = '';
      if (this.currentModal === 'editEntry') {
        ret = this.tileObject;
      }
      return ret;
    },
  },
  methods: {
    addCategory() {
      this.$store.dispatch('modal/setAndShowModal', {
        name: 'CategoryAddModal',
      });
    },
  },
});
</script>

<style lang="stylus">
.portal-categories
  position: relative;
  padding: calc(4 * var(--layout-spacing-unit)) calc(6 * var(--layout-spacing-unit));

  &__add
    margin-top: -50px;

  &__add-button
    vertical-align: top
    @extend .icon-button--admin

    svg
      vertical-align: top

  &__title
    cursor: pointer
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

  &__menu-parent
    background: var(--color-grey0)
    padding: 0.3em 0.5em;
    min-width: var(--app-tile-side-length)
    font-size: 16px

    &:hover
      background: #000
      cursor: pointer

    &:first-of-type
      border-radius: 8px 8px 0 0
    &:last-of-type
      border-radius: 0 0 8px 8px

.portal-iframes
  position: fixed;
  top: var(--portal-header-height);
  border: 0px solid var(--color-grey8);
  border-top-width: var(--portal-header-to-content-seperator-height);
  right: 0;
  bottom: 0;
  left: 0;
  background-color: #fff;

</style>
