export default function addLanguageTile(portalLanguageData) {
  const menuTitle = {
    de_DE: 'Sprache ändern',
    en_US: 'Change Language',
    fr_FR: 'Changer de langue',
  };

  const subMenuItems = portalLanguageData.map((element) => ({
    title: { en_US: element.label },
    linkTarget: 'internalFunction',
    internalFunction: (tileClick) => {
      tileClick.$store.dispatch('locale/setLocale', element.id.replace('-', '_'));
      return false;
    },
    links: [],
  }));

  const menuElement = {
    title: menuTitle,
    linkTarget: 'samewindow',
    subMenu: subMenuItems,
  };
  return menuElement;
}
