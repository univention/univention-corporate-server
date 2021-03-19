// https://docs.cypress.io/api/introduction/api.html

describe('General Tests', () => {
  it('Loads the page', () => {
    // stuff selenium can't do #1: mock requests / responses
    cy.intercept('GET', 'portal/portal.json', { fixture: 'portal.json' });
    cy.intercept('GET', 'meta.json', { fixture: 'meta.json' });
    cy.intercept('GET', 'de.json', { fixture: 'de.json' });
    cy.visit('/');
    cy.contains('h2', 'Verwaltung');
  });
});
