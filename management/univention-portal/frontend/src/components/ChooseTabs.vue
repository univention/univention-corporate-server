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
        :i18n-title-key="CHOOSE_TAB"
        data-test="choose-tabs"
        @cancel="cancel"
      >
        <div
          v-for="(tab, index) in tabs"
          :key="index"
          class="choose-tab"
          :class="{'choose-tab--active': isActiveTab(index)}"
        >
          <div
            :id="`choose-tab__button--${index + 1}`"
            :ref="activeTab === 0 && index === 0 || activeTab === index + 1 ? 'currentTab' : ''"
            class="choose-tab__button"
            tabindex="0"
            @click.prevent="gotoTab(index)"
            @keydown.enter.prevent="gotoTab(index)"
          >
            <div class="choose-tab__logo-wrapper">
              <img
                :src="tab.logo"
                onerror="this.src='./questionMark.svg'"
                alt=""
                class="choose-tab__img"
              >
            </div>
            {{ tab.tabLabel }}
            <span
              v-if="isActiveTab(index)"
              class="sr-only sr-only-mobile"
            >
              {{ ACTIVE }}
            </span>
          </div>
          <icon-button
            icon="x"
            :active-at="['modal']"
            :aria-label-prop="ariaLabelCloseTab(tab.tabLabel)"
            :data-test="`chooseTabCloseButton--${index + 1}`"
            @click="closeTab(index)"
          />
        </div>
      </modal-dialog>
    </modal-wrapper>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';
import _ from '@/jsHelper/translate';

import ModalDialog from '@/components/modal/ModalDialog.vue';
import ModalWrapper from '@/components/modal/ModalWrapper.vue';
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
    CHOOSE_TAB(): string {
      return _('Choose a tab');
    },
    ACTIVE(): string {
      return `: ${_('active')}`;
    },
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
      return `${tabLabel} ${_('Select')}`;
    },
    ariaLabelCloseTab(tabLabel: string): string {
      return `${tabLabel} ${_('Close')}`;
    },
    closeTab(index: number) {
      this.$store.dispatch('tabs/deleteTab', index + 1);
      if (this.tabs.length === 0) {
        this.$store.dispatch('navigation/setActiveButton', '');
      }
    },
    gotoTab(index: number) {
      this.$store.dispatch('tabs/setActiveTab', index + 1);
      this.cancel();
    },
    cancel() {
      this.$store.dispatch('navigation/setActiveButton', '');
    },
    isActiveTab(index: number): boolean {
      return this.activeTab === index + 1;
    },
  },
});
</script>
<style lang="stylus">
.choose-tab
  display: flex
  align-items: center
  position:relative
  margin: 2px 0
  border-radius: var(--border-radius-interactable)
  width: 20rem

  @media $mqSmartphone
    max-width: 100%

  &:first-of-type
    margin-top: 0.2rem

  &--active
    background-color: var(--bgc-apptile-default)

    & ^[0]__logo-wrapper
      background-color: none

  &__button
    display: flex
    align-items: center
    cursor: pointer
    border: 2px solid transparent
    padding: var(--layout-spacing-unit)
    padding-left: 0
    width: 100%

    &:focus
      outline: 0

      &:before
        border-color: var(--color-focus)

    &:before
      content: ''
      width: auto
      height: 100%
      position: absolute
      left: 0
      right: 0
      border: 2px solid transparent

  &__img
    width: 80%
    max-height: 80%
    vertical-align: middle
    border: 0

  &__logo-wrapper
    background-color: var(--bgc-apptile-default)
    border-radius: var(--border-radius-apptile)
    height: calc(var(--portal-header-height) * var(--portal-header-icon-scale))
    width: @height
    min-width: @height
    display: flex
    align-items: center
    justify-content: center
    margin: 0 var(--layout-spacing-unit-small) 0 0

  .icon-button
    margin-left: var(--layout-spacing-unit)
</style>
