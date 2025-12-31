<!--
SPDX-FileCopyrightText: 2021-2026 Univention GmbH
SPDX-License-Identifier: AGPL-3.0-only
-->
<template>
  <!-- TODO Semantic headlines -->
  <div
    ref="searchInput"
    class="portal-search"
  >
    <transition
      name="slide"
      appear
    >
      <flyout-wrapper
        v-if="activeButton === 'search'"
        :is-visible="activeButton === 'search'"
        class="portal-search__wrapper"
      >
        <input
          id="portal-search-input"
          ref="portalSearchInput"
          v-model="portalSearch"
          data-test="searchInput"
          type="text"
          class="portal-search__input"
          :aria-label="SEARCH"
          @input="searchTiles"
          @keyup.esc="closeSearchInput()"
        >
      </flyout-wrapper>
    </transition>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';
import _ from '@/jsHelper/translate';

import FlyoutWrapper from '@/components/navigation/FlyoutWrapper.vue';

interface PortalSearchData {
  portalSearch: string,
}

export default defineComponent({
  name: 'PortalSearch',
  components: { FlyoutWrapper },
  data(): PortalSearchData {
    return { portalSearch: '' };
  },
  computed: {
    ...mapGetters({
      activeButton: 'navigation/getActiveButton',
    }),
    SEARCH(): string {
      return _('search');
    },
  },
  mounted() {
    this.$nextTick(() => {
      (this.$refs.portalSearchInput as HTMLElement).focus();
    });
  },
  beforeUnmount() {
    this.$store.dispatch('search/setSearchQuery', '');
  },
  methods: {
    searchTiles(): void {
      this.$store.dispatch('search/setSearchQuery', this.portalSearch.toLowerCase());
      this.$nextTick(() => {
        const num = document.querySelectorAll('.portal-tile').length.toString();
        this.$store.dispatch('activity/setMessage', _('%(num)s search results', { num }));
      });
    },
    closeSearchInput(): void {
      this.$store.dispatch('activity/setRegion', 'portal-header');
      this.$store.dispatch('navigation/setActiveButton', '');
    },
  },
});
</script>

<style lang="stylus">
.portal-search
  &__input
    width: 100%;
    border: 0.1rem solid transparent;
    border-radius: var(--border-radius-interactable);
    background-color: var(--bgc-inputfield-on-body)
    padding: var(--layout-spacing-unit) !important;
    box-sizing: border-box;
    margin-bottom: 0

    &:focus
      border-color: var(--color-focus);
      outline: none;
  &__wrapper
    background-color: rgba(0,0,0,0)
    bottom: unset

.slide-enter-active,
.slide-leave-active {
  transition: transform 0.5s ease;
}

.slide-enter-from,
.slide-leave-to {
  transform: translateX(22rem)
}
</style>
