// https://docs.cypress.io/api/introduction/api.html

describe('General Tests', () => {
  it('Loads the page', () => {
    // stuff selenium can't do #1: mock requests / responses
    cy.intercept('GET', 'portal/portal.json', { fixture: 'portal.json' });
    cy.intercept('GET', 'meta.json', { fixture: 'meta.json' });
    cy.intercept('GET', 'de.json', { fixture: 'de.json' });
    cy.intercept('GET', 'languages.json', { fixture: 'languages.json' });

    cy.visit('/');
    /**
     * Since there are few data-test attributes the selectors are all over the place,
     * this is quite common but not a best practice. So this is good for learning but
     * should be refactored.
     */
    cy.contains('h2', 'Verwaltung');
    // Tiles?
    cy.get('.portal-tile__name').contains('span', 'Univention Blog');
    // Login notification?
    cy.get('.notification-bubble__title').contains('Anmelden');
    // Buttons ?
    cy.get('button[aria-label="Button for Searchbar"]');
    cy.get('button[aria-label="Open notifications"]');
    cy.get('button[aria-label="Button for navigation"]');
  });
});
