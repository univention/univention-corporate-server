<template>
  <div class="portal-search">
    <input
      ref="portalSearchInput"
      v-model="portalSearch"
      type="text"
      class="portal-search__input"
      @input="searchTiles"
      @keyup.esc="closeSearchInput()"
    >
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';

interface PortalSearchData {
  portalSearch: string,
}

export default defineComponent({
  name: 'PortalSearch',
  data(): PortalSearchData {
    return {
      portalSearch: '',
    };
  },
  computed: {
    ...mapGetters({
      originalArray: 'categories/getCategories',
      modalState: 'modal/modalState',
      searchQuery: 'search/searchQuery',
    }),
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
    },
    closeSearchInput(): void {
      this.$store.dispatch('navigation/setActiveButton', '');
    },
  },
});
</script>

<style lang="stylus">
.portal-search {
  &__input {
    height: 5.8rem;
    width: 100%;
    background-color: transparent;
    color: #fff;
    border: 1px solid white;
    border-radius: var(--border-radius-interactable);
    __border-radius: var(--border-radius-interactable);
    font-size: 2rem;
    padding-left: 2rem;
    box-sizing: border-box;

    &:focus {
      border-color: var(--color-primary);
      outline: none;
    }
  }
}
</style>
