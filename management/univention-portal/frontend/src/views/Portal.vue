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

    <!-- <portal-standby /> -->

    <portal-tool-tip
      v-if="tooltip"
      v-bind="tooltip"
    />

    <portal-modal
      :is-active="modalState"
      @click="closeModal"
    >
      <component
        :is="modalComponent"
        v-bind="modalProps"
      />
    </portal-modal>

    <portal-modal
      v-if="showAdminModal"
      :is-active="showAdminModal"
    >
      <div class="portal-category__modal">
        <modal-admin
          :show-title-button="false"
          :modal-debugging="true"
          modal-title="ADD_CATEGORY"
          variant="category"
          modal-type="addNewCategory"
          save-action="saveCategory"
          @closeModal="closeModal"
          @saveCategory="saveCategory"
        />
      </div>
    </portal-modal>
    <cookie-banner />
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';

import PortalIframe from '@/components/PortalIframe.vue';
import ChangePassword from '@/components/forms/ChangePassword.vue';
import PortalToolTip from '@/components/PortalToolTip.vue';
import PortalCategory from '@/components/PortalCategory.vue';
// import PortalIcon from '@/components/globals/PortalIcon.vue';
import PortalHeader from '@/components/PortalHeader.vue';
import PortalFolder from '@/components/PortalFolder.vue';
import PortalModal from '@/components/globals/PortalModal.vue';
import ModalAdmin from '@/components/admin/ModalAdmin.vue';

import PortalBackground from '@/components/PortalBackground.vue';
import PortalStandby from '@/components/PortalStandby.vue';
import CookieBanner from '@/components/CookieBanner.vue';
import HeaderButton from '@/components/navigation/HeaderButton.vue';

import notificationMixin from '@/mixins/notificationMixin.vue';

import Translate from '@/i18n/Translate.vue';

// mocks
import PopMenuDataCategories from '@/assets/data/popmenuCategories.json';

interface PortalViewData {
  buttonIcon: string,
  ariaLabelButton: string,
  popMenuShow: boolean,
  popMenuCategories: unknown,
  showAdminModal: boolean,
}

export default defineComponent({
  name: 'Portal',
  components: {
    PortalCategory,
    PortalFolder,
    PortalHeader,
    ChangePassword,
    // PortalIcon,
    PortalIframe,
    PortalToolTip,
    PortalModal,
    ModalAdmin,
    PortalBackground,
    PortalStandby,
    CookieBanner,
    HeaderButton,
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
    };
  },
  computed: {
    ...mapGetters({
      categories: 'categories/getCategories',
      modalState: 'modal/modalState',
      modalComponent: 'modal/modalComponent',
      modalProps: 'modal/modalProps',
      modalStubborn: 'modal/modalStubborn',
      tabs: 'tabs/allTabs',
      activeTabIndex: 'tabs/activeTabIndex',
      editMode: 'portalData/editMode',
      tooltip: 'tooltip/tooltip',
    }),
  },
  methods: {
    closeModal(): void {
      if (!this.modalStubborn) {
        this.$store.dispatch('modal/setHideModal');
      }
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
      // open modal
    },
    saveCategory(value) {
      // save the changes
      console.log('save category: ', value);

      this.closeModal();
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
    user-select: none

    display: inline-block
    margin-right: 1em

    width: 2em
    height: 2em
    background-color: var(--color-grey0)
    background-size: 1em
    background-repeat: no-repeat
    background-position: center
    border-radius: 50%
    box-shadow: var(--box-shadow)

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
