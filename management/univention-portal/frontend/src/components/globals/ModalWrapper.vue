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
      class="modal-wrapper"
      :class="{ 'modal-wrapper--isVisible': isActive }"
      @click.self="$emit('backgroundClick');"
    >
      <slot />
    </div>
  </teleport>
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
  },
  emits: ['backgroundClick'],
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

    &--isVisible
      z-index: $zindex-0
      background-color: rgba(51, 51, 49, 0.5);
      display: flex
      align-items: center
      justify-content: center

      &> *
        position: relative
        z-index: 1
</style>
