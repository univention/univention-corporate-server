function makeEntry(entryID, availableTiles, availableFolders, defaultLinkTarget) {
  let entry = availableTiles.find((tile) => tile.dn === entryID);
  if (entry) {
    return {
      title: entry.name,
      description: entry.description,
      links: entry.links,
      linkTarget: entry.linkTarget === 'useportaldefault' ? defaultLinkTarget : entry.linkTarget,
      pathToLogo: entry.logo_name,
    };
  }
  entry = availableFolders.find((folder) => folder.dn === entryID);
  return {
    title: entry.name,
    subMenu: entry.entries.map((folderEntryID) => makeEntry(folderEntryID, availableTiles, availableFolders, defaultLinkTarget)),
  };
}

export default function createMenuStructure(portalData) {
  const portalMenuLinks = portalData.menu_links;
  const availableTiles = portalData.entries;
  const availableFolders = portalData.folders;
  const { defaultLinkTarget } = portalData.portal;

  return portalMenuLinks.map((menuID) => makeEntry(menuID, availableTiles, availableFolders, defaultLinkTarget));
}
