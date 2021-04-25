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
  <div class="portal-modal">
    <modal-wrapper
      :is-active="true"
      @backgroundClick="cancel"
    >
      <modal-dialog
        i18n-title-key="CHOOSE_TAB"
        @cancel="cancel"
      >
        <div
          v-for="(tab, idx) in tabs"
          :key="idx"
          class="choose-tab"
        >
          <button
            class="choose-tab__button"
            type="button"
            @click="gotoTab(idx)"
          >
            <img
              :src="tab.logo"
              onerror="this.src='./questionMark.svg'"
              alt=""
            >
            {{ tab.tabLabel }}
          </button>
          <icon-button
            icon="x"
            @click="closeTab(idx)"
          />
        </div>
      </modal-dialog>
    </modal-wrapper>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';

import ModalDialog from '@/components/ModalDialog.vue';
import ModalWrapper from '@/components/globals/ModalWrapper.vue';
import IconButton from '@/components/globals/IconButton.vue';

export default defineComponent({
  name: 'ChooseTabs',
  components: {
    ModalDialog,
    ModalWrapper,
    IconButton,
  },
  computed: {
    ...mapGetters({
      tabs: 'tabs/allTabs',
    }),
  },
  methods: {
    closeTab(idx: number) {
      this.$store.dispatch('tabs/deleteTab', idx + 1);
      if (this.tabs.length === 0) {
        this.$store.dispatch('navigation/setActiveButton', '');
      }
    },
    gotoTab(idx: number) {
      this.$store.dispatch('tabs/setActiveTab', idx + 1);
      this.cancel();
    },
    cancel() {
      this.$store.dispatch('navigation/setActiveButton', '');
    },
  },
});
</script>
<style lang="stylus">
.choose-tab
  margin-top: calc(4 * var(--layout-spacing-unit))
  padding: var(--layout-spacing-unit)
  display: flex
  background-color: var(--color-grey25)
  border-radius: var(--border-radius-container)

  &__button
    text-transform: none

    img
      height: var(--button-size)
      margin-right: calc(4 * var(--layout-spacing-unit))

  .icon-button
    margin-left: auto
</style>
