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

    <div
      v-show="!activeTabIndex"
      class="portal-categories"
    >
      <template v-if="categories">
        <portal-category
          v-for="(category, index) in categories"
          :key="index"
          :title="category.title"
          :tiles="category.tiles"
          :drop-zone="index"
          :category-index="index"
        />
      </template>

      <h2
        v-if="editMode"
        class="portal-categories__title"
        @click.prevent="addCategory()"
      >
        <header-button
          :icon="buttonIcon"
          :aria-label="ariaLabelButton"
          :no-click="true"
          class="portal-categories__add-button"
        />
        <translate i18n-key="ADD_CATEGORY" />
      </h2>

      <div
        v-if="popMenuShow"
        class="portal-categories__menu-wrapper portal-categories__add"
      >
        <div class="portal-categories__menu-container">
          <div
            v-for="(item, index) in popMenuCategories"
            :key="index"
            class="portal-categories__menu-parent"
          >
            <span
              class="portal-categories__menu-title"
              @click="openAdminModal(item.action)"
            >
              {{ $localized(item.title) }}
            </span>
          </div>
        </div>
      </div>
    </div>

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

    <modal-wrapper
      v-if="showAdminModal"
      :is-active="showAdminModal"
    >
      <div class="portal-category__modal">
        <modal-admin
          :show-title-button="false"
          :modal-debugging="true"
          :modal-type="adminModalAction"
          modal-title="ADD_CATEGORY"
          variant="category"
          save-action="saveCategory"
          @closeModal="closeAdminModal"
          @saveCategory="saveCategory"
        />
      </div>
    </modal-wrapper>

    <portal-sidebar />
    <portal-modal />
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';

import HeaderButton from '@/components/navigation/HeaderButton.vue';
import ModalAdmin from '@/components/admin/ModalAdmin.vue';
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

// mocks
import PopMenuDataCategories from '@/assets/data/popmenuCategories.json';

// Temp interface for menu data mock
interface PopMenuCategory {
  title: Record<string, string>,
  action: string
}

interface PortalViewData {
  buttonIcon: string,
  ariaLabelButton: string,
  popMenuShow: boolean,
  popMenuCategories: Array<PopMenuCategory>,
  showAdminModal: boolean,
  adminModalAction: string,
}

export default defineComponent({
  name: 'Portal',
  components: {
    HeaderButton,
    ModalAdmin,
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
  data(): PortalViewData {
    return {
      buttonIcon: 'plus',
      ariaLabelButton: 'Button for adding a new category',
      popMenuShow: false,
      popMenuCategories: PopMenuDataCategories,
      showAdminModal: false,
      adminModalAction: '',
    };
  },
  computed: {
    ...mapGetters({
      categories: 'categories/getCategories',
      tabs: 'tabs/allTabs',
      activeTabIndex: 'tabs/activeTabIndex',
      editMode: 'portalData/editMode',
      tooltip: 'tooltip/tooltip',
    }),
  },
  methods: {
    closeAdminModal(): void {
      if (this.showAdminModal) {
        this.showAdminModal = false;
      }
    },
    addCategory() {
      console.log('addCategory');
      this.popMenuShow = !this.popMenuShow;
    },
    openAdminModal(action) {
      console.log('openAdminModal: ', action);
      this.popMenuShow = false;
      this.showAdminModal = true;
      this.adminModalAction = action;
      // open modal
    },
    saveCategory(value) {
      // save the changes
      console.log('save category: ', value);
      this.closeAdminModal();
    },
  },
});
</script>

<style lang="stylus">
.portal-categories
  position: relative;
  padding: calc(7 * var(--layout-spacing-unit)) calc(6 * var(--layout-spacing-unit));

  &__add
    margin-top: -50px;

  &__add-button
    @extend .icon-button--admin

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
