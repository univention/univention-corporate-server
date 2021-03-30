// Iframes are inherently unsafe. Don't use them.

describe('General Tests', () => {
  it('search shows results with "Blog"', () => {
    cy.setCookie('UMCLang', 'de_DE');
    // stuff selenium can't do #1: mock requests / responses
    cy.intercept('GET', 'portal.json', { fixture: 'portal_logged_out.json' });
    // cy.intercept('GET', 'portal/portal.json', { fixture: 'portal_logged_in.json' });
    cy.intercept('GET', 'meta.json', { fixture: 'meta.json' });
    cy.intercept('GET', 'de.json', { fixture: 'de.json' });
    cy.intercept('GET', 'languages.json', { fixture: 'languages.json' });
    cy.visit('/');
    cy.contains('Cookie-Einstellungen');
    cy.get('.cookie-banner__button-text').click();
    cy.getCookie('univentionCookieSettingsAccepted').should('exist');


    const searchButton = cy.get('[data-test="searchbutton"]');
    
    searchButton.should('not.have.class', 'header-button--is-active');
  
    cy.get('[data-test="searchInput"]').should('not.be.visible'); // input exists after searchButton is clicked
    
    cy.get('[data-test="searchbutton"]').click();
    searchButton.should('have.class', 'header-button--is-active');
    cy.get('[data-test="searchInput"]').should('exist');
    cy.get('[data-test="searchInput"]');

    cy.contains('Handbuch');
    cy.get('[data-test="searchInput"]').type('Blog');
    cy.contains('Handbuch').should('not.exist');
    cy.contains('Blog');
  });
  it('searches also for tile description', () => {
      // how to write test for description? Tooltip is not redered. 
  });
});
