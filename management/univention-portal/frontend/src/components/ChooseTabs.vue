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
          <div
            :ref="activeTab === 0 && idx === 0 || activeTab === idx + 1 ? 'currentTab' : ''"
            class="choose-tab__button"
            tabindex="0"
            :aria-label="ariaLabelChooseTab(tab.tabLabel)"
            @click.prevent="gotoTab(idx)"
            @keydown.enter.prevent="gotoTab(idx)"
          >
            <img
              :src="tab.logo"
              onerror="this.src='./questionMark.svg'"
              alt=""
            >
            {{ tab.tabLabel }}
          </div>
          <icon-button
            icon="x"
            :active-at="['modal']"
            :aria-label-prop="ariaLabelCloseTab(tab.tabLabel)"
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
      activeTab: 'tabs/activeTabIndex',
    }),
  },
  watch: {
    activeTab(newIdx: number) {
      if (newIdx === 0) {
        this.cancel();
      }
    },
  },
  mounted() {
    this.$store.dispatch('activity/setLevel', 'modal');
    const el = this.$refs.currentTab as HTMLElement;
    el?.focus();
  },
  methods: {
    ariaLabelChooseTab(tabLabel: string): string {
      return `${tabLabel} ${this.$translateLabel('SELECT_TAB')}`;
    },
    ariaLabelCloseTab(tabLabel: string): string {
      return `${tabLabel} ${this.$translateLabel('CLOSE_TAB')}`;
    },
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
  display: flex
  align-items: center

  &:first-of-type
    margin-top: 0

  &__button
    display: flex
    background-color: var(--button-bgc)
    align-items: center
    cursor: pointer
    border: 2px solid transparent
    border-radius: var(--border-radius-container)
    padding: var(--layout-spacing-unit)
    width: 100%

    &:focus, &:active, &:hover
      border-color: var(--color-focus)

    img
      height: var(--button-size)
      margin-right: var(--layout-spacing-unit)

  .icon-button
    margin-left: var(--layout-spacing-unit)
</style>
