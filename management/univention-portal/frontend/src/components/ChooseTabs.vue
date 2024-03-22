<!--
Copyright 2021-2024 Univention GmbH

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
          :key="tab.id"
          class="choose-tab"
          :class="{'choose-tab--active': activeTabId === tab.id}"
        >
          <div
            :id="`choose-tab__button--${tab.id}`"
            :ref="(activeTabId === 0 && index === 0) || activeTabId === tab.id ? 'currentTab' : ''"
            class="choose-tab__button"
            tabindex="0"
            @click.prevent="gotoTab(tab.id)"
            @keydown.enter.prevent="gotoTab(tab.id)"
          >
            <div
              class="choose-tab__logo-wrapper"
              :style="tab.backgroundColor ? `background: ${tab.backgroundColor}` : ''"
            >
              <img
                :src="tab.logo"
                onerror="this.src='./questionMark.svg'"
                alt=""
                class="choose-tab__img"
              >
            </div>
            {{ tab.tabLabel }}
            <span
              v-if="activeTabId === tab.id"
              class="sr-only sr-only-mobile"
            >
              {{ ACTIVE }}
            </span>
          </div>
          <icon-button
            icon="x"
            class="button--flat button--icon--tab-style"
            :active-at="['modal']"
            :aria-label-prop="ariaLabelCloseTab(tab.tabLabel)"
            :data-test="`chooseTabCloseButton--${tab.id}`"
            @click="closeTab(tab.id)"
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
      activeTabId: 'tabs/activeTabId',
    }),
    CHOOSE_TAB(): string {
      return _('Choose a tab');
    },
    ACTIVE(): string {
      return `: ${_('active')}`;
    },
  },
  watch: {
    activeTabId(newId: number) {
      if (newId === 0) {
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
    closeTab(id: number) {
      this.$store.dispatch('tabs/deleteTab', id);
      if (this.tabs.length === 0) {
        this.$store.dispatch('navigation/setActiveButton', '');
      }
    },
    gotoTab(id: number) {
      this.$store.dispatch('tabs/setActiveTab', id);
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
  display: flex
  align-items: center
  position:relative
  margin: var(--layout-spacing-unit-small) 0
  padding: var(--layout-spacing-unit)
  border-radius: var(--border-radius-interactable)
  width: 20rem
  transition: background-color var(--portal-transition-duration) ease
  background: var(--portal-tab-background)

  &:hover
    background-color: var(--portal-tab-background-hover)

  @media $mqSmartphone
    max-width: 100%

  &:first-of-type
    margin-top: 0.2rem

  &--active
    background-color: var(--portal-tab-background-active)

  &__button
    display: flex
    align-items: center
    cursor: pointer
    border: 2px solid transparent
    width: 100%

    &:focus-visible
      outline: 0

      &:before
        border-color: var(--color-focus)
        border-radius: var(--button-border-radius)

    &:before
      content: ''
      width: auto
      height: 100%
      position: absolute
      left: 0
      right: 0
      border: 0.2rem solid transparent

  &__img
    width: 80%
    max-height: 80%
    vertical-align: middle
    border: 0

  &__logo-wrapper
    background-color: var(--bgc-apptile-default)
    border-radius: var(--border-radius-apptile)
    height: var(--button-size)
    width: @height
    min-width: @height
    display: flex
    align-items: center
    justify-content: center
    margin: 0 var(--layout-spacing-unit) 0 0

  .button--icon
    margin-left: var(--layout-spacing-unit)
</style>
