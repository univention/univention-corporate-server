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
<script>
import { mapGetters } from 'vuex';
import bestLink from '@/jsHelper/bestLink';

const tileClickMixin = {
  props: {
    links: {
      type: Array,
      required: true,
    },
    backgroundColor: {
      type: String,
      default: '',
    },
    linkTarget: {
      type: String,
    },
    pathToLogo: {
      type: String,
      required: false,
      default: './questionMark.svg',
    },
    internalFunction: {
      type: Function,
      required: false,
    },
  },
  computed: {
    ...mapGetters({
      metaData: 'metaData/getMeta',
      editMode: 'portalData/editMode',
      locale: 'locale/getLocale',
    }),
    link() {
      return bestLink(this.links, this.metaData.fqdn, this.locale);
    },
    anchorTarget() {
      if (this.editMode || this.linkTarget !== 'newwindow') {
        return null;
      }
      return '_blank';
    },
  },
  emits: [
    'clickAction',
  ],
  methods: {
    tileClick(evt) {
      if (this.editMode) {
        evt.preventDefault();
        this.editTile();
        return false;
      }
      if (this.minified) {
        evt.preventDefault();
        return false;
      }
      this.$store.dispatch('tooltip/unsetTooltip');
      // this.$store.dispatch('modal/hideAndClearModal');
      if (this.linkTarget === 'internalFunction') {
        evt.preventDefault();
        return this.internalFunction(this);
      }
      if (!this.link) {
        return false;
      }
      if (this.linkTarget === 'embedded') {
        evt.preventDefault();
        this.openEmbedded();
        // return false;
      }
      this.$emit('clickAction');
      return true;
    },
    openEmbedded() {
      const tab = {
        tabLabel: this.$localized(this.title),
        backgroundColor: this.backgroundColor,
        logo: this.pathToLogo,
        iframeLink: this.link,
      };
      this.$store.dispatch('navigation/setActiveButton', '');
      this.$store.dispatch('tabs/addTab', tab);
      this.$store.dispatch('modal/hideAndClearModal');
      this.$store.dispatch('modal/hideAndClearModal');
      this.$store.dispatch('tooltip/setHoverOnTooltip', false);
      this.$store.dispatch('tooltip/unsetTooltip');
    },
  },
};

export default tileClickMixin;
</script>
<style>
</style>
