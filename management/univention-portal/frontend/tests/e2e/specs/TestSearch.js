beforeEach(() => {
  cy.setCookie('UMCLang', 'de_DE');
  // stuff selenium can't do #1: mock requests / responses
  cy.intercept('GET', 'portal.json', { fixture: 'portal_logged_out.json' });
  // cy.intercept('GET', 'portal/portal.json', { fixture: 'portal_logged_in.json' });
  cy.intercept('GET', 'meta.json', { fixture: 'meta.json' });
  cy.intercept('GET', 'de.json', { fixture: 'de.json' });
  cy.intercept('GET', 'languages.json', { fixture: 'languages.json' });
  cy.visit('/');
  cy.setCookie('univentionCookieSettingsAccepted', 'simpleCookieValue');
});

describe('General Tests', () => {
  it('Tile title in results should match with the String "Blog"', () => {
    // make inputfield visible 
    clickOnSearchButton();

    // test for tilename
    cy.contains('Handbuch');
    cy.get('[data-test="searchInput"]').type('Blog');
    cy.contains('Handbuch').should('not.exist');
    cy.contains('Blog');
  });


  it('Searches also for tile description', () => {
    // make inputfield visible 
    clickOnSearchButton();

    cy.get('.portal-tile').first().contains('ownCloud');
    cy.get('[data-test="searchInput"]').type('Univention Management Console zur Ver­wal­tung der UCS-Domäne und des lokalen Systems');
    cy.get('.portal-tile').first().contains('System- und Domäneneinstellungen');
  });
});

const clickOnSearchButton = () => {
  cy.get('[data-test="searchbutton"]').should('not.have.class', 'header-button--is-active');
  cy.get('[data-test="searchInput"]').should('not.exist'); // input exists after searchButton is clicked
  cy.get('[data-test="searchbutton"]').click();
  cy.get('[data-test="searchbutton"]').should('have.class', 'header-button--is-active');
  cy.get('[data-test="searchInput"]').should('exist');
}