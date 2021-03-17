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
      required: true,
    },
  },
  computed: {
    ...mapGetters({
      metaData: 'meta/getMeta',
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
      if (!this.link) {
        return false;
      }
      if (this.editMode) {
        evt.preventDefault();

        // TODO: start edit tile dialog
        return false;
      }
      if (this.inFolder) {
        evt.preventDefault();
        return false;
      }
      this.$emit('clickAction');
      if (this.linkTarget === 'embedded') {
        evt.preventDefault();
        this.openEmbedded();
        return false;
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
