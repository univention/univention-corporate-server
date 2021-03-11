function makeEntry(entryID, availableTiles, availableFolders, defaultLinkTarget) {
  let entry = availableTiles.find((tile) => tile.dn === entryID);
  if (entry) {
  // TODO: remove id once the service is offering the right data.
    return {
      id: entry.name.en_US,
      title: entry.name,
      description: entry.description,
      links: entry.links,
      linkTarget: entry.linkTarget === 'useportaldefault' ? defaultLinkTarget : entry.linkTarget,
      pathToLogo: entry.logo_name,
    };
  }
  entry = availableFolders.find((folder) => folder.dn === entryID);
  // TODO: remove id once the service is offering the right data.
  return {
    id: entry.name.en_US,
    title: entry.name,
    tiles: entry.entries.map((folderEntryID) => makeEntry(folderEntryID, availableTiles, availableFolders, defaultLinkTarget)),
  };
}

export default function createCategories(portalData) {
  const portalContent = portalData.portal.content;
  const availableCategories = portalData.categories;
  const availableTiles = portalData.entries;
  const availableFolders = portalData.folders;
  const { defaultLinkTarget } = portalData.portal;

  return portalContent.map(([categoryID, categoryEntries]) => {
    // console.log(categoryID, categoryEntries);
    const category = availableCategories.find((cat) => cat.dn === categoryID);
    const tiles = categoryEntries.map((entryID) => makeEntry(entryID, availableTiles, availableFolders, defaultLinkTarget));
    return {
      title: category.display_name,
      tiles,
    };
  });
}
