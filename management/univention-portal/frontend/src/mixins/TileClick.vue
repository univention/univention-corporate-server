<script>
import { mapGetters } from 'vuex';
import bestLink from '@/jsHelper/bestLink';

const tileClickMixin = {
  props: {
    links: {
      type: Array,
      required: true,
    },
    linkTarget: {
      type: String,
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
      return bestLink(this.links, this.metaData.fqdn, this.locale.split('_')[0]);
    },
  },
  emits: [
    'clickAction',
  ],
  methods: {
    tileClick(evt) {
      if (this.editMode) {
        evt.preventDefault();

        // TODO: start edit tile dialog
        return false;
      }
      if (this.inFolder) {
        evt.preventDefault();
        return false;
      }
      if (this.linkTarget === 'internalFunction') {
        return this.internalFunction(this);
      }
      if (!this.link) {
        return false;
      }
      if (this.linkTarget === 'embedded') {
        evt.preventDefault();
        this.openEmbedded();
        this.$emit('clickAction');
        // return false;
      }
      return true;
    },
    openEmbedded() {
      const tab = {
        tabLabel: this.$localized(this.title),
        logo: this.pathToLogo,
        iframeLink: this.link,
      };
      this.$store.dispatch('tabs/addTab', tab);
    },
  },
};

export default tileClickMixin;
</script>
