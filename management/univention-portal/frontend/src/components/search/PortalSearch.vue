<!--
Copyright 2021-2022 Univention GmbH

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
      modalState: 'modal/modalState',
      searchQuery: 'search/searchQuery',
      emptySearchResults: 'search/emptySearchResults',
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
        this.$store.dispatch('activity/addMessage', {
          id: 'search',
          msg: _('%(num)s search results', { num }),
        });
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
    min-height: auto

.slide-enter-active,
.slide-leave-active {
  transition: transform 0.5s ease;
}

.slide-enter-from,
.slide-leave-to {
  transform: translateX(22rem)
}
</style>
