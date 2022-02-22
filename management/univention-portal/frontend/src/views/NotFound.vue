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
  <div class="not-found">
    <screen-reader-announcer />
    <portal-background />
    <portal-header />
    <portal-sidebar />
    <notifications :is-in-notification-bar="false" />
    <portal-error :error-type="404" />

    <router-view />
    <loading-overlay />
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';
import _ from '@/jsHelper/translate';

import IconButton from '@/components/globals/IconButton.vue';
import Region from '@/components/activity/Region.vue';
import ModalWrapper from '@/components/modal/ModalWrapper.vue';
import Notifications from 'components/notifications/Notifications.vue';
import PortalBackground from '@/components/PortalBackground.vue';
import PortalCategory from 'components/PortalCategory.vue';
import PortalHeader from '@/components/PortalHeader.vue';
import PortalIframe from 'components/PortalIframe.vue';
import PortalModal from 'components/modal/PortalModal.vue';
import PortalSidebar from '@/components/PortalSidebar.vue';
import PortalToolTip from 'components/PortalToolTip.vue';
import ScreenReaderAnnouncer from '@/components/globals/ScreenReaderAnnouncer.vue';
import PortalError from '@/components/globals/PortalError.vue';
import LoadingOverlay from '@/components/globals/LoadingOverlay.vue';

export default defineComponent({
  name: 'NotFound',
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
    ScreenReaderAnnouncer,
    PortalError,
  },
  computed: {
    ...mapGetters({
      portalFinalLayout: 'portalData/portalFinalLayout',
      errorContentType: 'portalData/errorContentType',
      tabs: 'tabs/allTabs',
      activeTabIndex: 'tabs/activeTabIndex',
      editMode: 'portalData/editMode',
      tooltip: 'tooltip/tooltip',
      metaData: 'metaData/getMeta',
      getModalState: 'modal/getModalState',
      userState: 'user/userState',
    }),
    ADD_CATEGORY(): string {
      return _('Add category');
    },
    isSecondModalActive(): boolean {
      return this.getModalState('secondLevelModal');
    },
    portalRole(): string {
      return this.editMode ? 'application' : '';
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
  border: 0 solid var(--portal-tab-background)
  border-top-width: var(--layout-height-header-separator)
  right: 0
  bottom: 0
  left: 0

</style>
