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
import { Options, Vue } from 'vue-class-component';
import { mapGetters } from 'vuex';

@Options({
  name: 'PortalSearch',
  mounted() {
    this.$nextTick(() => {
      this.$refs.portalSearchInput.focus();
    });
  },
  data() {
    return {
      portalSearch: '',
    };
  },
  beforeUnmount() {
    this.$store.dispatch('search/setSearchQuery', '');
  },
  computed: {
    ...mapGetters({
      originalArray: 'categories/categoryState',
      modalState: 'modal/modalState',
      searchQuery: 'search/searchQuery',
    }),
  },
  methods: {
    searchTiles() {
      this.$store.dispatch('search/setSearchQuery', this.portalSearch.toLowerCase());
    },
    closeSearchInput() {
      this.$store.dispatch('navigation/setActiveButton', '');
    },
  },
})

export default class PortalSearch extends Vue {}
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
