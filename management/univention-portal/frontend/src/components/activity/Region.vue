<!--
  SPDX-FileCopyrightText: 2021-2026 Univention GmbH
  SPDX-License-Identifier: AGPL-3.0-only
-->
<template>
  <component
    :is="tag"
    :id="id"
    :role="ariaRole"
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
    ariaRole: {
      type: String,
      default: '',
    },
    direction: {
      type: String,
      default: 'leftright',
    },
  },
  computed: {
    ...mapGetters({
      inDragnDropMode: 'dragndrop/inDragnDropMode',
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
    goUp(ev?: KeyboardEvent): void {
      if (document.activeElement?.id === 'portal-search-input') {
        return;
      }
      if (this.inDragnDropMode) {
        return;
      }
      if (this.direction === 'topdown') {
        ev?.preventDefault();
        if (!this.focusPrev(ev)) {
          this.focusLast(ev);
        }
      }
    },
    goDown(ev?: KeyboardEvent): void {
      if (document.activeElement?.id === 'portal-search-input') {
        return;
      }
      if (this.inDragnDropMode) {
        return;
      }
      if (this.direction === 'topdown') {
        ev?.preventDefault();
        if (!this.focusNext(ev)) {
          this.focusFirst(ev);
        }
      }
    },
    goLeft(ev?: KeyboardEvent): void {
      if (document.activeElement?.id === 'portal-search-input') {
        return;
      }
      if (this.inDragnDropMode) {
        return;
      }
      if (this.direction === 'leftright') {
        ev?.preventDefault();
        if (!this.focusPrev(ev)) {
          this.focusLast(ev);
        }
      }
    },
    goRight(ev?: KeyboardEvent): void {
      if (document.activeElement?.id === 'portal-search-input') {
        return;
      }
      if (this.inDragnDropMode) {
        return;
      }
      if (this.direction === 'leftright') {
        ev?.preventDefault();
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
    focusLast(ev?: KeyboardEvent): boolean {
      const activeElements = this.$el.querySelectorAll('[tabindex="0"][id]');
      const activeElem = activeElements[activeElements.length - 1];
      const elem = document.getElementById(activeElem?.id);
      return this.focusElem(elem, ev);
    },
    focusNext(ev?: KeyboardEvent): boolean {
      const elem = this.findNext();
      return this.focusElem(elem, ev);
    },
    focusPrev(ev?: KeyboardEvent): boolean {
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
