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
  <teleport to="body">
    <div
      class="portal-tooltip"
      role="tooltip"
      data-test="portal-tooltip"
    >
      <div
        class="portal-tooltip__header"
      >
        <div
          class="portal-tooltip__thumbnail"
          :style="backgroundColor ? `background: ${backgroundColor}` : ''"
        >
          <img
            :src="icon || './questionMark.svg'"
            onerror="this.src='./questionMark.svg'"
            alt=""
            class="portal-tooltip__logo"
          >
        </div>
        <div class="portal-tooltip__title">
          {{ title }}
        </div>
        <icon-button
          icon="x"
          class="portal-tooltip__close-icon"
          :aria-label-prop="CLOSE_TOOLTIP"
          @click="closeToolTip()"
        />
      </div>

      <!-- eslint-disable vue/no-v-html -->
      <div
        v-if="description"
        :id="ariaId"
        class="portal-tooltip__description"
        v-html="description"
      />
    <!-- eslint-enable vue/no-v-html -->
    </div>
  </teleport>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import _ from '@/jsHelper/translate';

import IconButton from '@/components/globals/IconButton.vue';

export default defineComponent({
  name: 'PortalToolTip',
  components: {
    IconButton,
  },
  props: {
    title: {
      type: String,
      default: '',
    },
    icon: {
      type: String,
      default: './questionMark.svg',
    },
    backgroundColor: {
      type: String,
      default: '',
    },
    description: {
      type: String,
      default: '',
    },
    ariaId: {
      type: String,
      default: '',
    },
  },
  computed: {
    CLOSE_TOOLTIP(): string {
      return _('Close Tooltip');
    },
  },
  methods: {
    closeToolTip() {
      this.$store.dispatch('tooltip/unsetTooltip');
    },
  },
});
</script>

<style lang="stylus">
.portal-tooltip
  position: fixed
  bottom: calc(2 * var(--layout-spacing-unit))
  right: calc(2 * var(--layout-spacing-unit))
  background-color: var(--bgc-content-container)
  border-radius: var(--border-radius-container)
  min-width: calc(20 * 1rem)
  max-width: calc(20 * 1rem)
  padding: calc(2 * var(--layout-spacing-unit))
  box-shadow: var(--box-shadow)
  z-index: $zindex-3
  display: block
  pointer-events: none
  animation: fadeIn 1s
  -webkit-animation: fadeIn 1s
  -moz-animation: fadeIn 1s
  -o-animation: fadeIn 1s
  -ms-animation: fadeIn 1s
  @keyframes fadeIn {
  0% {opacity:0;}
  100% {opacity:1;}
  }

  @-moz-keyframes fadeIn {
    0% {opacity:0;}
    100% {opacity:1;}
  }

  @-webkit-keyframes fadeIn {
    0% {opacity:0;}
    100% {opacity:1;}
  }

  @-o-keyframes fadeIn {
    0% {opacity:0;}
    100% {opacity:1;}
  }

  @-ms-keyframes fadeIn {
    0% {opacity:0;}
    100% {opacity:1;}
  }
  @media $mqSmartphone
    bottom: unset;
    top: calc(3 * var(--layout-spacing-unit))
    min-width: 4rem
    max-width: 84vw
    width: 90%
    left:0
    right:0
    margin-left:auto
    margin-right:auto
    font-size: var(--font-size-5)
    pointer-events: auto

  &__header
    display: flex
    align-items: center
    margin-bottom: 1rem

    @media $mqSmartphone
      margin-bottom: calc(1 * var(--layout-spacing-unit))

  &__thumbnail
    border-radius: var(--border-radius-apptile)
    display: flex
    align-items: center
    justify-content: center
    box-shadow: 0 0.3rem 0.6rem rgba(0, 0, 0, 0.16)
    background-color: var(--bgc-apptile-default)

    .portal-tooltip__header &
      width: calc(3 * 1rem)
      height: calc(3 * 1rem)
      margin-right: calc(3 * calc(1rem / 2))

      @media $mqSmartphone
        height: calc(4 * var(--layout-spacing-unit))
        width: @height
        margin-right: calc(1 * var(--layout-spacing-unit))

  &__logo
    width: 80%
    max-height: 80%
    vertical-align: middle
    border: 0

  &__close-icon
    display: none

    @media $mqSmartphone
      display: block
      margin-left: auto
</style>
