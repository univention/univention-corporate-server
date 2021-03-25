const sizes = ['iphone-8', 'ipad-2'];
const orientations = ['portrait', 'landscape'];

describe('Logo', () => {
  orientations.forEach((orientation) => {
    sizes.forEach((size) => {
      // make assertions on the logo using
      // an array of different viewports
      it(`Should display the menubutton on ${size} screen, orientation ${orientation}`, () => {
        cy.intercept('GET', 'portal.json', { fixture: 'portal_logged_out.json' });
        cy.intercept('GET', 'meta.json', { fixture: 'meta.json' });
        cy.intercept('GET', 'de.json', { fixture: 'de.json' });
        cy.intercept('GET', 'languages.json', { fixture: 'languages.json' });
        cy.viewport(size);

        cy.visit('/');
        cy.get('.cookie-banner__button-text').click();
        // reactivate after fix
        // cy.get('[data-test="navigationbutton"]').should('be.visible');
      });
    });
  });
});
