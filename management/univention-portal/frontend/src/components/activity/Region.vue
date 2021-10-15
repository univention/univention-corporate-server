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
  <component
    :is="tag"
    :id="id"
    @keydown.left.exact="goLeft"
    @keydown.right.exact="goRight"
    @keydown.up.exact="goUp"
    @keydown.down.exact="goDown"
  >
    <slot />
  </component>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';

export default defineComponent({
  name: 'Region',
  props: {
    id: {
      type: String,
      required: true,
    },
    role: {
      type: String,
      default: 'region',
    },
    direction: {
      type: String,
      default: 'leftright',
    },
  },
  computed: {
    ...mapGetters({
      inDragnDropMode: 'dragndrop/inDragnDropMode',
      activityLevel: 'activity/level',
      activityRegion: 'activity/region',
      focus: 'activity/focus',
    }),
    tag() {
      if (this.role === 'none') {
        return 'div';
      }
      if (this.role === 'banner') {
        return 'header';
      }
      if (this.role === 'navigation') {
        return 'nav';
      }
      if (this.role === 'main') {
        return 'main';
      }
      return 'section';
    },
    active(): boolean {
      return this.activityRegion === this.id;
    },
  },
  watch: {
    active(oldValue, newValue) {
      if (newValue) {
        this.restoreFocus();
      }
    },
  },
  created() {
    this.$store.dispatch('activity/addRegion', this.id);
  },
  methods: {
    restoreFocus(): void {
      const id = this.focus[this.id];
      const elem = document.getElementById(id);
      if (!this.focusElem(elem)) {
        this.focusFirst();
      }
    },
    goUp(ev: KeyboardEvent): void {
      if (this.inDragnDropMode) {
        return;
      }
      if (this.direction === 'topdown') {
        ev.preventDefault();
        if (!this.focusPrev(ev)) {
          this.focusLast(ev);
        }
      }
    },
    goDown(ev: KeyboardEvent): void {
      if (this.inDragnDropMode) {
        return;
      }
      if (this.direction === 'topdown') {
        ev.preventDefault();
        if (!this.focusNext(ev)) {
          this.focusFirst(ev);
        }
      }
    },
    goLeft(ev: KeyboardEvent): void {
      if (this.inDragnDropMode) {
        return;
      }
      if (this.direction === 'leftright') {
        ev.preventDefault();
        if (!this.focusPrev(ev)) {
          this.focusLast(ev);
        }
      }
    },
    goRight(ev: KeyboardEvent): void {
      if (this.inDragnDropMode) {
        return;
      }
      if (this.direction === 'leftright') {
        ev.preventDefault();
        if (!this.focusNext(ev)) {
          this.focusFirst(ev);
        }
      }
    },
    focusElem(elem: HTMLElement | null, ev?: KeyboardEvent): boolean {
      if (elem) {
        this.$store.dispatch('activity/saveFocus', {
          region: this.id,
          id: elem.id,
        });
        elem.focus();
        ev?.stopPropagation();
        ev?.preventDefault();
        return true;
      }
      return false;
    },
    focusFirst(ev?: KeyboardEvent): boolean {
      const activeElem = this.$el.querySelector('[tabindex="0"][id]');
      const elem = document.getElementById(activeElem?.id);
      return this.focusElem(elem, ev);
    },
    focusLast(ev: KeyboardEvent): boolean {
      const activeElements = this.$el.querySelectorAll('[tabindex="0"][id]');
      const activeElem = activeElements[activeElements.length - 1];
      const elem = document.getElementById(activeElem?.id);
      return this.focusElem(elem, ev);
    },
    focusNext(ev: KeyboardEvent): boolean {
      const elem = this.findNext();
      return this.focusElem(elem, ev);
    },
    focusPrev(ev: KeyboardEvent): boolean {
      const elem = this.findPrev();
      return this.focusElem(elem, ev);
    },
    findPrev(): HTMLElement | null {
      const activeElements = this.$el.querySelectorAll('[tabindex="0"]:not([hidden])');
      let elem: HTMLElement | null = null;
      let found = false;
      const activeId = document.activeElement?.id;
      activeElements.forEach((activeElem) => {
        if (activeElem.id === activeId) {
          found = true;
        }
        if (!found && activeElem.id) {
          elem = document.getElementById(activeElem.id);
        }
      });
      if (found) {
        return elem;
      }
      return null;
    },
    findNext(): HTMLElement | null {
      const activeElements = this.$el.querySelectorAll('[tabindex="0"]:not([hidden])');
      let elem: HTMLElement | null = null;
      let found = false;
      const activeId = document.activeElement?.id;
      activeElements.forEach((activeElem) => {
        if (found && activeElem.id) {
          elem = document.getElementById(activeElem.id);
        }
        found = activeElem.id === activeId;
      });
      return elem;
    },
  },
});
</script>
<style>
</style>
