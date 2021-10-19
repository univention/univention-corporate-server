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
<script>
import { mapGetters } from 'vuex';

const draggableMixin = {
  computed: {
    ...mapGetters({
      inDragnDropMode: 'dragndrop/inDragnDropMode',
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
        this.dragstart();
      }
    },
    dragKeyboardDirection(evt, direction) {
      if (!this.inDragnDropMode) {
        return;
      }
      evt.preventDefault();

      this.$store.dispatch('portalData/changeLayoutDirection', {
        fromId: this.layoutId,
        direction,
      });
      // FIXME with scrollIntoView the page jumps to the bottom after
      // portalData/saveLayout
      evt.target.scrollIntoView({
        behavior: 'auto',
        block: 'center',
      });
      if (direction === 'left' || direction === 'up') {
        this.$nextTick(() => {
          evt.target.focus();
        });
      }
    },
    handleTabWhileMoving() {
      if (this.isBeingDragged) {
        this.$store.dispatch('portalData/saveLayout');
      }
    },
    dragstart() {
      if (!this.isDraggable) {
        return;
      }

      this.$store.dispatch('dragndrop/startDragging', {
        layoutId: this.layoutId,
        draggedType: this.draggedType(),
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
      this.$store.dispatch('dragndrop/cancelDragging');
    },
  },
};

export default draggableMixin;
</script>
<style>
</style>
