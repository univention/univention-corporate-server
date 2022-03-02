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
  <teleport
    v-if="teleportToBody"
    to="body"
  >
    <div
      :id="setID"
      :class="{ 'modal-wrapper': !isActive, 'modal-wrapper--isVisible': isActive,
                'modal-wrapper--isVisibleFullscreen': isActive && full, 'modal-wrapper--isSecondLayer': isSecondModalActive }"
      @click.self="$emit('backgroundClick', $event);"
    >
      <slot />
    </div>
  </teleport>
  <div v-else>
    <div
      :class="{ 'modal-wrapper': !isActive, 'modal-wrapper--isVisible': isActive,
                'modal-wrapper--isVisibleFullscreen': isActive && full, 'modal-wrapper--isSecondLayer': isSecondModalActive }"
      @click.self="$emit('backgroundClick', $event);"
    >
      <slot />
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';

export default defineComponent({
  name: 'ModalWrapper',
  props: {
    isActive: {
      type: Boolean,
      required: true,
    },
    full: {
      type: Boolean,
      default: false,
    },
    modalLevel: {
      type: Number,
      default: 1,
    },
    teleportToBody: {
      type: Boolean,
      default: true,
    },
  },
  emits: ['backgroundClick'],
  computed: {
    isSecondModalActive(): boolean {
      return this.modalLevel === 2 && this.isActive;
    },
    setID(): string | null {
      return this.isActive ? 'modal-wrapper--isVisible' : null;
    },
  },
});
</script>

<style lang="stylus">
.modal-wrapper
    position: fixed;
    width: 100%;
    height: 100%;
    top: 0;
    right: 0;
    bottom: 0;
    left: 0;
    z-index: -999
    opacity: 0
    transition: opacity 0.5s ease;

    &--isVisible
      position: fixed;
      width: 100%;
      height: 100%;
      top: 0;
      right: 0;
      bottom: 0;
      left: 0;
      z-index: $zindex-2
      background-color: var(--bgc-underlay);
      display: flex
      align-items: center
      justify-content: center
      opacity: 1
      transition: opacity 0.5s ease;

      &> *
        position: relative
        z-index: 1

    &--isSecondLayer
      z-index: $zindex-3

      &> *
        position: relative
        z-index: 1

    &--isVisibleFullscreen
      z-index: $zindex-4
</style>
