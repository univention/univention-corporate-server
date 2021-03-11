<template>
  <div>
    <component
      :is="wrapperTag"
      :href="link"
      :target="setLinkTarget"
      :aria-describedby="createID()"
      class="portal-tile"
      data-test="tileLink"
      @mouseover="editMode || showTooltip()"
      @mouseleave="hideTooltip"
      @mousedown="hideTooltip"
      @click="tileClick"
      @keydown.tab.exact="setFocus($event, 'forward')"
      @keydown.shift.tab.exact="setFocus($event, 'backward')"
      @focus="showTooltip()"
      @blur="hideTooltip()"
    >
      <div
        :style="`background: ${backgroundColor}`"
        :class="[
          'portal-tile__box', { 'portal-tile__box--dragable': editMode }
        ]"
      >
        <img
          :src="pathToLogo"
          onerror="this.src='./questionMark.svg'"
          :alt="`Logo ${$localized(title)}`"
          class="portal-tile__img"
        >
      </div>
      <span
        class="portal-tile__name"
        @click.prevent="tileClick"
      >
        {{ $localized(title) }}
      </span>

      <header-button
        v-if="!noEdit && isAdmin"
        :icon="buttonIcon"
        :aria-label="ariaLabelButton"
        :no-click="true"
        class="portal-tile__edit-button"
        @click.prevent="editTile()"
      />
    </component>
    <portal-tool-tip
      :title="$localized(title)"
      :icon="pathToLogo"
      :description="$localized(description)"
      :aria-id="createID()"
      :is-displayed="isActive"
    />
  </div>
</template>

<script lang="ts">
import { Options, Vue } from 'vue-class-component';

import PortalToolTip from '@/components/PortalToolTip.vue';
import TileClick from '@/mixins/TileClick.vue';
import HeaderButton from '@/components/navigation/HeaderButton.vue';

import bestLink from '@/jsHelper/bestLink';

@Options({
  name: 'PortalTile',
  components: {
    PortalToolTip,
    HeaderButton,
  },
  mixins: [
    TileClick,
  ],
  props: {
    title: {
      type: Object,
      required: true,
    },
    description: {
      type: Object,
      required: true,
    },
    pathToLogo: {
      type: String,
      required: false,
      default: 'questionMark.svg',
    },
    backgroundColor: {
      type: String,
      default: 'var(--color-grey40)',
    },
    inFolder: {
      type: Boolean,
      default: false,
    },
    hasFocus: {
      type: Boolean,
      default: false,
    },
    lastElement: {
      type: Boolean,
      default: false,
    },
    firstElement: {
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
  emits: ['makeStuff'],
  data() {
    return {
      isActive: false,
    };
  },
  mounted() {
    if (this.hasFocus) {
      this.$el.children[0].focus(); // sets focus to first Element in opened Folder
    }
  },
  computed: {
    wrapperTag(): string {
      return (this.inFolder || this.editMode) ? 'div' : 'a';
    },
    link(): string {
      return this.links ? bestLink(this.links, this.metaData.fqdn) : '';
    },
    setLinkTarget(): string | null {
      if (this.editMode || this.linkTarget !== 'newwindow') {
        return null;
      }
      return '_blank';
    },
  },
  methods: {
    hideTooltip(): void {
      this.isActive = false;
    },
    showTooltip(): void {
      if (!this.inFolder) {
        this.isActive = true;
      }
    },
    setFocus(event, direction): void {
      if (this.lastElement && direction === 'forward') {
        event.preventDefault();
        this.$emit('makeStuff', 'focusFirst');
      } else if (this.firstElement && direction === 'backward') {
        event.preventDefault();
        this.$emit('makeStuff', 'focusLast');
      }
    },
    editTile() {
      console.log('editTile');
    },
    showToolTipIfFocused() {
      if (this.isActive) {
        this.hideTooltip();
      } else {
        this.showTooltip();
      }
    },
    createID() {
      return `element-${this.$.uid}`;
    },
  },
})
export default class PortalTile extends Vue {
  title!: Record<string, string>;

  description!: Record<string, string>;

  links!: string[];

  pathToLogo?: string;

  backgroundColor = 'var(--color-grey40)';
}
</script>

<style lang="stylus">
.portal-tile
  position: relative
  outline: 0
  width: var(--app-tile-side-length)
  display: flex
  flex-direction: column
  align-items: center
  cursor: pointer
  color: var(--font-color-contrast-high)
  text-decoration: none

  &:hover
    color: var(--font-color-contrast-high)
    text-decoration: none

  &__box
    border-radius: 15%
    display: flex
    align-items: center
    justify-content: center
    box-shadow: var(--box-shadow)
    background: var(--color-grey40)
    width: var(--app-tile-side-length)
    height: @width
    margin-bottom: calc(2 * var(--layout-spacing-unit))
    border: 0.2rem solid transparent

    ~/:focus &
      border-color: var(--color-primary)

    &--dragable
      position: relative

      &:after
        content: ' ';
        position: absolute;
        top: 0;
        right: 0;
        bottom: 0;
        left: 0;
        z-index: $zindex-1;

  &__img
    width: 80%

  &__name
    text-align: center
    width: 100%
    overflow: hidden
    text-overflow: ellipsis
    white-space: nowrap

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

    &--in-modal
      position relative

// current fix for edit button in modal
.portal-folder__in-modal
  & .portal-tile__edit-button
    display: none
</style>
