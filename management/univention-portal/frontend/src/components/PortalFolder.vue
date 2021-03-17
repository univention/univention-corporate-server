<template>
  <div
    v-if="hasTiles"
    class="portal-folder"
    :class="{ 'portal-folder__in-modal': inModal }"
  >
    <button
      class="portal-tile__box"
      tabindex="0"
      @click="openFolder"
      @keypress.enter="openFolder"
      @keyup.esc.stop="closeFolder()"
    >
      <div class="portal-folder__thumbnails">
        <div
          v-for="(tile, index) in tiles"
          :key="index"
        >
          <portal-tile
            :ref="'portalFolderChildren' + index"
            v-bind="tile"
            :in-folder="!inModal"
            :has-focus="setFocus(index)"
            :last-element="isLastElement(index, tiles)"
            :first-element="isFirstElement(index, tiles)"
            :no-edit="true"
            @keepFocusInFolderModal="keepFocusInFolderModal"
            @clickAction="closeFolder"
          />
        </div>
      </div>
    </button>
    <span class="portal-folder__name">
      {{ $localized(title) }}
    </span>
    <header-button
      v-if="!noEdit && isAdmin && !inModal"
      :icon="buttonIcon"
      :aria-label="ariaLabelButton"
      :no-click="true"
      class="portal-folder__edit-button"
      @click.prevent="editFolder()"
    />
  </div>
</template>

<script lang="ts">
import { defineComponent, PropType } from 'vue';

import PortalTile from '@/components/PortalTile.vue';
import PortalModal from '@/components/globals/PortalModal.vue';
import HeaderButton from '@/components/navigation/HeaderButton.vue';
import { Title, Tile } from '@/store/models';

export default defineComponent({
  name: 'PortalFolder',
  components: {
    PortalTile,
    // TODO: Very strange behavior:
    // PortalModal component is not being used here,
    // but removing it moves the Sidebar to the middle
    // eslint-disable-next-line vue/no-unused-components
    PortalModal,
    HeaderButton,
  },
  props: {
    title: {
      type: Object as PropType<Title>,
      required: true,
    },
    tiles: {
      type: Array as PropType<Tile[]>,
      required: true,
    },
    inModal: {
      type: Boolean,
      default: false,
    },
    isAdmin: {
      type: Boolean,
      default: false,
    },
    noEdit: {
      type: Boolean,
      default: false,
    },
    buttonIcon: {
      type: String,
      default: 'edit-2',
    },
    ariaLabelButton: {
      type: String,
      default: 'Tab Aria Label',
    },
  },
  computed: {
    hasTiles(): boolean {
      return this.tiles.length > 0;
    },
  },
  methods: {
    closeFolder(): void {
      this.$store.dispatch('modal/setHideModal');
    },
    openFolder() {
      if (this.inModal) {
        return;
      }
      this.$store.dispatch('modal/setShowModal', {
        name: 'PortalFolder',
        props: { ...this.$props, inModal: true },
      });
    },
    setFocus(index): boolean {
      return this.inModal && index === 0;
    },
    isLastElement(index, array): boolean {
      return index === (array.length - 1);
    },
    isFirstElement(index): boolean {
      return index === 0;
    },
    getLastElement() {
      console.log('ELEMENT');
    },
    keepFocusInFolderModal(focusElement) {
      // TODO: Following $refs are bad practice and do not have proper typescript support
      const firstElement = (this.$refs.portalFolderChildren0 as HTMLFormElement).$el.children[0];
      const lastChild = `portalFolderChildren${this.tiles.length - 1}`;
      const lastElement = (this.$refs[lastChild] as HTMLFormElement).$el.children[0];

      if (focusElement === 'focusLast') {
        lastElement.focus();
      } else if (focusElement === 'focusFirst') {
        firstElement.focus();
      }
    },
    editFolder() {
      console.log('editFolder');
    },
  },
});
</script>

<style lang="stylus">
.portal-folder
  position: relative
  width: var(--app-tile-side-length)
  display: flex
  flex-direction: column
  align-items: center
  cursor: pointer

  &__name
    text-align: center
    width: 100%
    overflow: hidden
    text-overflow: ellipsis
    white-space: nowrap

  &__in-modal
    cursor: default

    .portal-tile
      &__box
        width: calc(5 * var(--app-tile-side-length))
        height: @width

        .portal-tile
          width: var(--app-tile-side-length)
          &__box
            width: var(--app-tile-side-length)
            height: @width
    .portal-folder__thumbnails .portal-tile__name
        display: block;

  &__thumbnails
    width: 80%;
    height: 80%;
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    grid-template-rows: repeat(3, 1fr);
    grid-gap: calc(4 * var(--layout-spacing-unit))
    grid-gap: var(--layout-spacing-unit)

    .portal-tile
      width: calc(0.2 * var(--app-tile-side-length))
      &__box
        width: calc(0.2 * var(--app-tile-side-length))
        height: @width
        margin-bottom: var(--layout-spacing-unit)

      &__name
        display: none;

  &__edit-button
    user-select: none

    position: absolute
    top: -0.75em
    right: -0.75em

    width: 2em
    height: 2em
    background-color: var(--color-grey0)
    background-size: 1em
    background-repeat: no-repeat
    background-position: center
    border-radius: 50%
    box-shadow: var(--box-shadow)

  .portal-tile__box
    background: var(--color-grey0)
    border: 0.2rem solid transparent

    &:focus
      border-color: var(--color-primary)
      outline: none;
</style>
