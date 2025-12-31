<!--
  SPDX-FileCopyrightText: 2021-2026 Univention GmbH
  SPDX-License-Identifier: AGPL-3.0-only
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
    box-shadow: var(--box-shadow)
    margin: 0 0 calc(2 * var(--layout-spacing-unit)) 0
    min-width: var(--app-tile-side-length)
    width: var(--app-tile-side-length)
    height: var(--app-tile-side-length)
    border-radius: var(--border-radius-apptile)
    border: 0.2rem solid var(--button-bgc)
    background-color: transparent
    cursor: pointer
    box-sizing: border-box
    transition: scale var(--portal-transition-duration) ease

    &:hover
      scale: 1.08

    &:focus-visible
      border-color: var(--color-focus)

    &:focus-visible, &:hover
      background-color: transparent

    svg
      width: 100%
      height: 100%
      stroke: var(--button-bgc)

  .portal-tile__name
    white-space: inherit
</style>
