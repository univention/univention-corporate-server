<template>
  <region
    v-if="subMenuVisible & (menuParent === parentIndex)"
    id="portal-sidenavigation-sub"
    role="navigation"
    direction="topdown"
    :aria-label="GO_BACK"
  >
    <menu-item
      :id="menuItem.id"
      :title="menuItem.title"
      :is-sub-item="true"
      :links="[]"
      class="portal-sidenavigation__menu-subItem portal-sidenavigation__menu-subItem--parent"
      @click="toggleMenu()"
      @keydown.enter.exact="toggleMenu()"
      @keydown.space.exact.prevent="toggleMenu()"
      @keydown.left.exact="toggleMenu()"
      @keydown.esc="closeNavigation"
    />
    <div
      v-for="(subItem, subindex) in menuItem.subMenu"
      :key="subindex"
      :class="subMenuClass"
    >
      <menu-item
        v-if="subMenuVisible & (menuParent === parentIndex)"
        :id="subItem.id"
        :ref="`subItem${subindex}`"
        :title="subItem.title"
        :links="subItem.links || []"
        :link-target="subItem.linkTarget"
        :path-to-logo="subItem.pathToLogo"
        :internal-function="subItem.internalFunction"
        :background-color="subItem.backgroundColor"
        class="portal-sidenavigation__menu-subItem"
        @clickAction="closeNavigation"
        @keydown.esc="closeNavigation"
      />
    </div>
  </region>
</template>
<script lang="ts">
import { defineComponent } from 'vue';
import _ from '@/jsHelper/translate';

import Region from '@/components/activity/Region.vue';
import MenuItem from '@/components/navigation/MenuItem.vue';

export default defineComponent({
  name: 'SubMenuItem',
  components: {
    MenuItem,
    Region,
  },
  props: {
    subMenuVisible: {
      type: Boolean,
      required: true,
    },
    menuParent: {
      type: Number,
      required: true,
    },
    parentIndex: {
      type: Number,
      required: true,
    },
    menuItem: {
      type: Object,
      required: true,
    },
    subMenuClass: {
      type: String,
      required: true,
    },
  },
  emits: ['toggleMenu'],
  computed: {
    GO_BACK(): string {
      return _('Go Back');
    },
  },
  methods: {
    toggleMenu(): void {
      this.$emit('toggleMenu');
    },
    closeNavigation(): void {
      this.$store.dispatch('navigation/setActiveButton', '');
      this.$store.dispatch('activity/setRegion', 'portal-header');
    },
  },
});
</script>
