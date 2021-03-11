<template>
  <div
    :class="{'portal-category--empty': (!editMode && !showCategoryHeadline) }"
    class="portal-category"
  >
    <h2
      v-if="editMode || showCategoryHeadline"
      class="portal-category__title"
      :class="!editMode || 'portal-category__title--edit'"
      @click.prevent="editMode ? editCategory() : ''"
    >
      <header-button
        v-if="editMode"
        :icon="buttonIcon"
        :aria-label="ariaLabelButton"
        :no-click="true"
        class="portal-category__edit-button"
      />
      {{ $localized(title) }}
    </h2>
    <div
      class="portal-category__tiles dragdrop__container"
      :class="{'portal-category__tiles--editmode': editMode}"
    >
      <template v-if="editMode">
        <draggable-wrapper
          v-model="vTiles"
          :drop-zone-id="dropZone"
          :data-drop-zone-id="dropZone"
          transition="10000"
          class="dragdrop__drop-zone"
        >
          <template #item="{ item }">
            <div class="dragdrop__draggable-item">
              <portal-tile
                v-if="isTile(item)"
                v-bind="item"
                :data-tile="$localized(item.title)"
                :title="item.title"
                :is-admin="true"
              />

              <portal-folder
                v-if="isFolder(item)"
                v-bind="item"
                :data-folder="$localized(item.title)"
                :is-admin="true"
              />
            </div>
          </template>
        </draggable-wrapper>
      </template>

      <template v-else>
        <template
          v-for="(tile, index) in tiles"
        >
          <div
            v-if="isTile(tile) || isFolder(tile)"
            :id="index"
            :key="index"
          >
            <portal-tile
              v-if="isTile(tile)"
              :ref="'tile' + index"
              v-bind="tile"
            />
            <portal-folder
              v-if="isFolder(tile)"
              v-bind="tile"
              :ref="'tile' + index"
            />
          </div>
        </template>
      </template>
    </div>

    <draggable-debugger
      v-if="editMode && debug"
      :items="vTiles"
    />
  </div>
</template>

<script lang="ts">
import { Options, Vue } from 'vue-class-component';
import { mapGetters } from 'vuex';

import PortalTile from '@/components/PortalTile.vue';
import PortalFolder from '@/components/PortalFolder.vue';

import HeaderButton from '@/components/navigation/HeaderButton.vue';

import DraggableWrapper from '@/components/dragdrop/DraggableWrapper.vue';
import DraggableDebugger from '@/components/dragdrop/DraggableDebugger.vue';

@Options({
  name: 'PortalCategory',
  components: {
    PortalTile,
    PortalFolder,
    HeaderButton,
    DraggableWrapper,
    DraggableDebugger,
  },
  props: {
    title: {
      type: Object,
      required: true,
    },
    tiles: {
      type: Array,
      required: true,
    },
    dropZone: {
      type: Number,
      required: true,
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
  data() {
    return {
      vTiles: this.tiles,
      isActive: false,
      debug: false, // `true` enables the debugger for the tiles array(s) in admin mode
      toolTip: {},
      showCategoryHeadline: false,
    };
  },
  mounted() {
    this.$nextTick(() => {
      this.hasTiles();
    });
  },
  updated() {
    this.hasTiles(this.tiles);
  },
  watch: {
    vTiles(val) {
      // TODO: save drag & drop changes
      console.info('saveState');
      console.log('val: ', val);
    },
  },
  computed: {
    ...mapGetters({
      editMode: 'portalData/editMode',
      searchQuery: 'search/searchQuery',
    }),
  },
  methods: {
    isTile(obj: PortalTile | PortalFolder): boolean {
      return 'linkTarget' in obj && this.tileMatchesQuery(obj);
    },
    isFolder(obj: PortalTile | PortalFolder): obj is PortalFolder {
      return 'tiles' in obj && this.folderMatchesQuery(obj);
    },
    changed() {
      console.log('changed');
    },
    editCategory() {
      console.log('editCategory');
    },
    tileMatchesQuery(obj: PortalTile | PortalFolder): boolean {
      return this.$localized(obj.title).toLowerCase()
        .includes(this.searchQuery.toLowerCase());
    },
    folderMatchesQuery(obj: PortalFolder): boolean {
      return this.tileMatchesQuery(obj) ||
        obj.tiles.some((tile) => this.$localized(tile.title).toLowerCase()
          .includes(this.searchQuery.toLowerCase()));
    },
    hasTiles() {
      const refArray = Object.entries(this.$refs);
      const children = refArray.filter((ref) => ref[1] !== null);
      if (children.length > 0) {
        this.showCategoryHeadline = true;
      } else {
        this.showCategoryHeadline = false;
      }
    },
  },
})

export default class PortalCategory extends Vue {
  title!: Record<string, string>;

  tiles!: Array<PortalTile>;
}
</script>

<style lang="stylus">
.portal-category
  margin-bottom: calc(10 * var(--layout-spacing-unit));

  &--empty {
    margin-bottom: 0;
  }

  &__tiles
    display: grid
    grid-template-columns: repeat(auto-fill, var(--app-tile-side-length))
    grid-gap: calc(6 * var(--layout-spacing-unit))

    &--editmode {
      display: block
    }

  &__drop-zone
    width: 100%;
    overflow: hidden;
    &--hidden
      display: none

  &__drag-element
    height: 210px
    width: 160px

  &__tile-dotted
    width: calc(20 * var(--layout-spacing-unit))
    height: calc(20 * var(--layout-spacing-unit))
    border-radius: 15%
    border: 3px dashed var(--color-grey40) !important

  &__edit-button
    user-select: none

    display: inline-block
    margin-right: 1em

    width: 2em
    height: 2em
    background-color: var(--color-grey0)
    background-size: 1em
    background-repeat: no-repeat
    background-position: center
    border-radius: 50%
    box-shadow: var(--box-shadow)

  &__title
    display: inline-block
    margin-top: 0
    margin-bottom: calc(6 * var(--layout-spacing-unit))

    &--edit
      cursor: pointer
</style>
