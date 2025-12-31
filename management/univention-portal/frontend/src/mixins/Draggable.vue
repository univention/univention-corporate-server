<!--
  SPDX-FileCopyrightText: 2021-2026 Univention GmbH
  SPDX-License-Identifier: AGPL-3.0-only
-->
<script>
import { mapGetters } from 'vuex';
import { DragType } from '@/store/modules/dragndrop';

const draggableMixin = {
  computed: {
    ...mapGetters({
      inDragnDropMode: 'dragndrop/inDragnDropMode',
      inKeyboardDragnDropMode: 'dragndrop/inKeyboardDragnDropMode',
      dragndropId: 'dragndrop/getId',
      editMode: 'portalData/editMode',
    }),
    isDraggable() {
      if (!this.editMode) {
        return false;
      }
      switch (this.$options.name) {
        case 'PortalTile':
          return !this.minified;
        case 'PortalFolder':
          return !this.inModal;
        case 'PortalCategory':
          return !this.virtual;
        case 'TileAdd':
        default:
          return false;
      }
    },
    isBeingDragged() {
      if (!this.isDraggable) {
        return false;
      }
      return this.dragndropId.layoutId === this.layoutId;
    },
    showMoveButtonWhileDragging() {
      return this.inKeyboardDragnDropMode ? this.isBeingDragged : true;
    },
    showEditButtonWhileDragging() {
      return !this.inKeyboardDragnDropMode;
    },
    canDragEnter() {
      if (this.forFolder !== undefined) {
        // TileAdd
        return true;
      }
      return this.isDraggable;
    },
  },
  methods: {
    draggedType() {
      let draggedType = 'tile';
      if (this.$options.name === 'PortalCategory') {
        draggedType = 'category';
      }
      return draggedType;
    },
    dragKeyboardClick() {
      if (this.isBeingDragged) {
        this.$store.dispatch('portalData/saveLayout');
      } else {
        this.dragstart(null, 'keyboard');
      }
    },
    dragKeyboardDirection(evt, direction) {
      if (!this.inDragnDropMode) {
        return;
      }
      evt.preventDefault();

      this.$store.dispatch('dragndrop/lastDir', direction);
      this.$store.dispatch('portalData/changeLayoutDirection', {
        fromId: this.layoutId,
        direction,
      });
      this.$nextTick(() => {
        this.handleDragFocus(evt.target, direction);
      });
    },
    handleDragFocus(elem, direction) {
      if (this.isBeingDragged) {
        const rect = elem.getBoundingClientRect();
        const offset = 200;
        if (rect.top !== 0) {
          if (direction === 'down' || direction === 'right') {
            if (rect.top + offset > window.innerHeight) {
              window.scrollBy(0, rect.top - window.innerHeight + offset);
            }
          }
          if (direction === 'up' || direction === 'left') {
            if (rect.top - offset < 0) {
              window.scrollBy(0, rect.top - offset);
            }
          }
        }
        // @ts-ignore
        elem.focus();
      }
    },
    handleTabWhileMoving() {
      if (this.isBeingDragged) {
        this.$store.dispatch('portalData/saveLayout');
      }
    },
    dragstart(evt, dragType) {
      if (!this.isDraggable) {
        return;
      }

      if (evt) {
        const draggedElement = evt.srcElement;
        const dragClone = draggedElement.cloneNode(true);
        document.body.appendChild(dragClone);
        dragClone.style.transform = 'rotate(0)';
        dragClone.style.position = 'absolute';
        dragClone.style.left = '-10000px';
        dragClone.id = 'dragndropCloneNode';
        if (dragClone.children[2]) {
          dragClone.removeChild(dragClone.children[2]);
        }
        evt.dataTransfer.setDragImage(dragClone, 75, 75);
      }

      this.$store.dispatch('dragndrop/startDragging', {
        layoutId: this.layoutId,
        draggedType: this.draggedType(),
        dragType,
        saveOriginalLayout: true,
      });
    },
    dragenter(evt) {
      if (!this.canDragEnter) {
        evt.preventDefault();
        return;
      }

      const data = this.$store.getters['dragndrop/getId'];
      if (data.draggedType !== this.draggedType()) {
        return;
      }

      const toIsAddTile = this.$options.name === 'TileAdd';
      const toId = toIsAddTile ? this.superLayoutId : this.layoutId;
      const position = toIsAddTile ? -1 : null;
      this.$store.dispatch('portalData/changeLayout', {
        fromId: data.layoutId,
        toId,
        position,
      });
    },
    dragend(evt) {
      // if dragend is called via esc key we want to stop
      // the event (if we are in drag mode)
      if (this.inDragnDropMode) {
        evt?.preventDefault();
        evt?.stopImmediatePropagation();
      }
      const clone = document.getElementById('dragndropCloneNode');
      clone?.remove();
      this.$store.dispatch('dragndrop/cancelDragging');
    },
  },
};

export default draggableMixin;
</script>
<style>
</style>
