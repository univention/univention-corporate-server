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
      dragndropId: 'dragndrop/getId',
    }),
    isDraggable() {
      return this.editMode && !this.minified && !this.inModal && !this.virtual;
    },
    isBeingDragged() {
      if (!this.isDraggable) {
        return false;
      }
      return this.dragndropId.dn === this.dn;
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
    dragstart() {
      if (!this.isDraggable) {
        return;
      }
      this.$store.dispatch('dragndrop/startDragging', {
        dn: this.dn,
        superDn: this.superDn,
        original: true,
      });
    },
    dragenter(e) {
      if (!this.canDragEnter) {
        e.preventDefault();
        return;
      }
      const data = this.$store.getters['dragndrop/getId'];
      const myCategory = this.superDn;
      const otherCategory = data.superDn;
      const myId = this.dn;
      const otherId = data.dn;
      if (myCategory !== otherCategory) {
        if (!myCategory || !otherCategory) {
          // dragging category over tile or vice versa
          return;
        }
        this.$store.dispatch('portalData/moveContent', {
          src: otherId,
          origin: otherCategory,
          dst: myId,
          cat: myCategory,
        });
        this.$store.dispatch('dragndrop/startDragging', {
          dn: otherId,
          superDn: myCategory,
          original: false,
        });
        return;
      }
      if (myId === otherId) {
        return;
      }
      this.$store.dispatch('portalData/reshuffleContent', {
        src: otherId,
        dst: myId,
        cat: myCategory,
      });
    },
    dragend(e) {
      if (!this.isDraggable) {
        e.preventDefault();
        return;
      }
      this.$store.dispatch('dragndrop/revert');
    },
  },
};

export default draggableMixin;
</script>
<style>
</style>
