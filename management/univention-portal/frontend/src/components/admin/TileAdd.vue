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
  <div class="tile-add">
    <icon-button
      icon="plus"
      :aria-label-prop="ADD_NEW_TILE"
      :active-at="activeAt"
      class="tile-add__button"
      @dragenter="dragenter"
      @click="showMenu()"
    />
    <span class="portal-tile__name">{{ ADD_NEW_TILE }}</span>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import _ from '@/jsHelper/translate';

import IconButton from '@/components/globals/IconButton.vue';
import Draggable from '@/mixins/Draggable.vue';

export default defineComponent({
  name: 'TileAdd',
  components: {
    IconButton,
  },
  mixins: [
    Draggable,
  ],
  props: {
    superLayoutId: {
      type: String,
      required: true,
    },
    superDn: {
      type: String,
      required: true,
    },
    forFolder: {
      type: Boolean,
      default: false,
    },
  },
  computed: {
    id(): string {
      return `addtile-${this.superLayoutId}`;
    },
    activeAt(): string[] {
      if (this.forFolder) {
        return ['modal'];
      }
      return ['portal'];
    },
    ADD_NEW_TILE():string {
      return _('Add new Tile');
    },
  },
  methods: {
    showMenu(): void {
      this.$store.dispatch('modal/setAndShowModal', {
        name: 'TileAddModal',
        props: {
          superDn: this.superDn,
          forFolder: this.forFolder,
        },
      });
      this.$store.dispatch('activity/setRegion', 'tile-add-modal');
    },
  },
});
</script>

<style lang="stylus">
.tile-add
  display: flex
  flex-direction: column
  align-items: center
  border: 0; // TODO: Remove when weird servercaching is fixed

  &__button
    margin: 0 0 calc(2 * var(--layout-spacing-unit)) 0
    min-width: var(--app-tile-side-length)
    width: var(--app-tile-side-length)
    height: var(--app-tile-side-length)
    border-radius: var(--border-radius-apptile)
    border: 0.2rem solid var(--button-bgc)
    background-color: transparent
    cursor: pointer
    box-sizing: border-box

    &:focus
      border-color: var(--color-focus)

    &:focus, &:hover
      background-color: transparent

    svg
      width: 100%
      height: 100%
      stroke: var(--button-bgc)

  .portal-tile__name
    white-space: inherit
</style>
