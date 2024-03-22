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
  <div
    :class="{ 'header-button--is-active': isActiveButton }"
    class="header-button"
    @click="toggleActiveButton"
    @keyup.esc.stop="emptyActiveButton"
  >
    <div
      role="presentation"
    >
      <tabindex-element
        :id="'header-button-' + icon"
        :ref="setRef"
        tag="button"
        :active-at="['portal', `header-${icon}`]"
        :aria-expanded="isActiveButton"
        :aria-label="ariaLabel"
        class="button--icon button--icon--circle button--icon--header-style button--flat "
      >
        <portal-icon
          :icon="icon"
        />
        <div
          v-if="counter"
          class="header-button__detail"
        >
          {{ counter }}
        </div>
      </tabindex-element>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import _ from '@/jsHelper/translate';

import TabindexElement from '@/components/activity/TabindexElement.vue';
import PortalIcon from '@/components/globals/PortalIcon.vue';

export default defineComponent({
  name: 'HeaderButton',
  components: {
    PortalIcon,
    TabindexElement,
  },
  props: {
    icon: {
      type: String,
      required: true,
    },
    ariaLabelProp: {
      type: String,
      required: true,
    },
    noClick: {
      type: Boolean,
      default: false,
    },
    counter: {
      type: Number,
      default: null,
    },
  },
  computed: {
    isActiveButton(): boolean {
      return this.$store.state.navigation.activeButton === this.icon;
    },
    setRef(): string {
      return `${this.icon}Reference`;
    },
    ariaLabel(): string {
      let ariaLabel = '';
      if (this.counter === null) {
        ariaLabel = this.ariaLabelProp;
      } else if (this.counter === 1) {
        ariaLabel = `${this.ariaLabelProp}: ${this.counter} ${_('item')}`;
      } else {
        ariaLabel = `${this.ariaLabelProp}: ${this.counter} ${_('items')}`;
      }
      return ariaLabel;
    },
  },
  methods: {
    toggleActiveButton(): void {
      if (!this.noClick) {
        if (this.isActiveButton) {
          this.$store.dispatch('navigation/setActiveButton', '');
        } else {
          this.$store.dispatch('navigation/setActiveButton', this.icon);
        }
      }
    },
    emptyActiveButton(): void {
      if (!this.noClick) {
        this.$store.dispatch('navigation/setActiveButton', '');
      }
    },
  },
});
</script>

<style lang="stylus">
.header-button
  margin: 0 var(--layout-spacing-unit-small)

  &--is-active
      z-index:1000
      svg
        color: var(--color-accent)

  &__detail
    position: absolute
    color: var(--bgc-content-header)
    background-color: var(--bgc-header-number-circle)
    font-size: var(--font-size-5)
    width: 1.6em
    height: 1.6em
    left: 2em
    top: -0.5em
    border-radius: var(--border-radius-circles)
    display: flex
    align-items: center
    justify-content: center
    pointer-events: none

#header-button-bell svg
#header-button-copy svg
  margin-right: 0!important
</style>
