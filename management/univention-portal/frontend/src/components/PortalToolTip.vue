<!--
Copyright 2021-2022 Univention GmbH

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
  <transition
    name="fade"
    appear
    @before-enter="beforeEnter"
    @after-enter="onAfterEnter"
    @leave="leave"
  >
    <div
      ref="toolTip"
      class="portal-tooltip"
      role="tooltip"
      data-test="portal-tooltip"
      :style="tooltipPosition"
      @mouseenter="keepTooltip()"
      @mouseleave="closeToolTip"
    >
      <div class="portal-tooltip__inner-wrap">
        <div
          v-if="!isMobile"
          class="portal-tooltip__arrow"
          data-test="portal-tooltip-arrow"
          :style="arrowPosition"
        />
        <div class="cheat" />
        <div
          class="portal-tooltip__header"
        >
          <template v-if="isMobile">
            <div
              class="portal-tooltip__thumbnail"
              data-test="portal-tooltip-image"
              :style="backgroundColor ? `background: ${backgroundColor}` : ''"
            >
              <img
                :src="icon || './questionMark.svg'"
                onerror="this.src='./questionMark.svg'"
                alt=""
                class="portal-tooltip__logo"
              >
            </div>
            <div
              class="portal-tooltip__title"
              data-test="portal-tooltip-title"
            >
              {{ title }}
            </div>
          </template>
          <icon-button
            icon="x"
            class="portal-tooltip__close-icon"
            data-test="portal-tooltip-close-icon"
            :aria-label-prop="CLOSE_TOOLTIP"
            @click="closeToolTip()"
          />
        </div>
        <!-- eslint-disable vue/no-v-html -->
        <div
          v-if="description"
          class="portal-tooltip__description"
          data-test="portal-tooltip-description"
          v-html="description"
        />
        <!-- eslint-enable vue/no-v-html -->
        <div class="portal-tooltip__link-type">
          {{ linkTypeText }}
          <portal-icon
            class="portal-tooltip__link-type-icon"
            :class="{'portal-tooltip__link-type-icon--same-tab': sameTab}"
            :icon="linkTypeIcon"
          />
        </div>
      </div>
    </div>
  </transition>
</template>

<script lang="ts">
import { defineComponent, PropType } from 'vue';
import _ from '@/jsHelper/translate';

import IconButton from '@/components/globals/IconButton.vue';
import PortalIcon from '@/components/globals/PortalIcon.vue';

interface Data {
  calculatedPosition: Record<string, number|string>,
}

export default defineComponent({
  name: 'PortalToolTip',
  components: {
    IconButton,
    PortalIcon,
  },
  props: {
    backgroundColor: {
      type: String,
      default: '',
    },
    title: {
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
    icon: {
      type: String,
      default: './questionMark.svg',
    },
    position: {
      type: Object as PropType<Record<string, number>>,
      required: true,
    },
    isMobile: {
      type: Boolean,
      required: true,
    },
    linkType: {
      type: Object as PropType<Record<string, string>>,
      required: true,
    },
  },
  data(): Data {
    return {
      calculatedPosition: {
        left: this.position.left,
        bottom: this.position.bottom,
        zone: 'REGULAR',
      },
    };
  },
  computed: {
    CLOSE_TOOLTIP(): string {
      return _('Close Tooltip');
    },
    tooltipPosition(): string {
      if (!this.isMobile) {
        this.calculatePosition();
        return `left:${this.calculatedPosition.left}px;`;
      }
      return '';
    },
    arrowPosition(): string {
      if (this.calculatedPosition.zone === 'RIGHT') {
        return 'top: -2rem; right: 0.5rem;';
      }
      if (this.calculatedPosition.zone === 'BOTTOM') {
        return 'bottom: -2rem; left: 0.2rem; transform: rotate(180deg);';
      }
      if (this.calculatedPosition.zone === 'BOTTOM_RIGHT') {
        return 'bottom: -2rem; right: 0.5rem; transform: rotate(180deg);';
      }
      return 'top: -2rem; left:  0.2rem;';
    },
    transitionClassEnter(): string {
      if (this.calculatedPosition.zone === 'BOTTOM') {
        return 'fade-enter-from-top';
      }
      return 'fade-enter-from';
    },
    transitionClassLeave(): string {
      if (this.calculatedPosition.zone === 'BOTTOM') {
        return 'fade-leave-from-top';
      }
      return 'fade-leave-from';
    },
    linkTypeText(): string {
      return this.linkType.label;
    },
    linkTypeIcon(): string {
      return this.linkType.icon;
    },
    sameTab(): boolean {
      return this.linkType.icon === 'sidebar';
    },
  },
  created(): void {
    window.addEventListener('scroll', this.handleScroll);
  },
  unmounted(): void {
    window.removeEventListener('scroll', this.handleScroll);
  },
  methods: {
    keepTooltip(): void {
      this.$store.dispatch('tooltip/setHoverOnTooltip', true);
    },
    closeToolTip() {
      this.$store.dispatch('tooltip/setHoverOnTooltip', false);
      this.$store.dispatch('tooltip/unsetTooltip');
    },
    beforeEnter(el): void {
      const prePosition = this.calculatedPosition.zone === 'BOTTOM' || this.calculatedPosition.zone === 'BOTTOM_RIGHT' ? -15 : 20;
      if (!this.isMobile) {
        if (this.calculatedPosition.zone === 'BOTTOM' || this.calculatedPosition.zone === 'BOTTOM_RIGHT') {
          el.style.bottom = `${(this.calculatedPosition.bottom as number) - prePosition}px`;
        } else {
          el.style.top = `${(this.calculatedPosition.bottom as number) + prePosition}px`;
        }
        el.style.transition = 'all 0.2s ease-out';
        el.style.transition = this.calculatedPosition.zone === 'BOTTOM' ? 'transform: translateY(-115px)' : 'transform: translateY(15px)';
        el.style.opacity = '0';
      }
    },
    onAfterEnter(el): void {
      if (!this.isMobile) {
        const correctedPosition = this.calculatedPosition.zone === 'BOTTOM' || this.calculatedPosition.zone === 'BOTTOM_RIGHT' ? 0 : 10;
        if (this.calculatedPosition.zone === 'BOTTOM' || this.calculatedPosition.zone === 'BOTTOM_RIGHT') {
          el.style.bottom = `${(this.calculatedPosition.bottom as number) + correctedPosition}px`;
        } else {
          el.style.top = `${(this.calculatedPosition.bottom as number) + correctedPosition}px`;
        }
        el.style.opacity = '1';
        el.style.transition = 'transform: translateY(0)';
      }
    },
    leave(el): void {
      if (!this.isMobile) {
        el.style.top = `${this.calculatedPosition.bottom}px`;
        el.style.transition = 'all 0.25s ease-out';
        el.style.transition = this.calculatedPosition.zone === 'BOTTOM' ? 'transform: translateY(-115px)' : 'transform: translateY(15px)';
        el.style.opacity = '0';
      }
    },
    calculatePosition(): void {
      const tile = document.querySelector<HTMLElement>('.portal-tile__root-element');
      if (tile) {
        const regularZone = {
          x: (window.innerWidth - tile?.offsetWidth * 2),
          y: (window.innerHeight - tile?.offsetHeight * 2),
        };
        if (this.position.x > regularZone.x && this.position.y <= regularZone.y) {
          this.calculatedPosition = {
            left: this.position.left - tile?.offsetWidth * 2,
            bottom: this.position.bottom,
            zone: 'RIGHT',
          };
        } else if (this.position.x <= regularZone.x && this.position.y > regularZone.y) {
          this.calculatedPosition = {
            bottom: window.innerHeight - (this.position.y - 20),
            left: this.position.left,
            zone: 'BOTTOM',
          };
        } else if (this.position.x > regularZone.x && this.position.y > regularZone.y) {
          this.calculatedPosition = {
            left: this.position.left - tile?.offsetWidth * 2,
            bottom: window.innerHeight - (this.position.y - 20),
            zone: 'BOTTOM_RIGHT',
          };
        }
      }
    },
    handleScroll(): void {
      this.$store.dispatch('tooltip/unsetTooltip');
    },
  },
});
</script>

<style lang="stylus">
.portal-tooltip
  position: fixed
  background-color: var(--bgc-content-container)
  border-radius: var(--border-radius-container)
  min-width: calc(20 * 1rem)
  max-width: calc(20 * 1rem)
  padding: calc(2 * var(--layout-spacing-unit))
  box-shadow: var(--box-shadow)
  z-index: $zindex-3
  z-index: 99999
  display: block
  border: 1px solid var(--font-color-contrast-high)

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

  &__arrow
    display: block
    position: absolute
    width: 0;
    height: 0;
    border: solid var(--layout-spacing-unit);
    border-color: transparent transparent var(--font-color-contrast-high) transparent;

  &__inner-wrap
    position: relative
    width: 100%
    height: 100%

  &__link-type
    text-align: right
    font-size: var(--font-size-5)
    display: flex
    align-items: center
    justify-content: flex-end
    margin-top: 0.3rem

  &__link-type-icon
    margin-left: 0.3rem
    width: 0.8rem
    &--same-tab
      transform: rotate(90deg)
  .cheat
    width: calc(100%);
    height: calc(100% + 75%);
    position absolute
    z-index: -1
    top: -38%;
    left: 0;

.fade-enter-active {
  transition: all 0.25s ease-out
}

.fade-leave-active {
  transition: all 0.25s cubic-bezier(1, 0.5, 0.8, 1)
}
</style>
