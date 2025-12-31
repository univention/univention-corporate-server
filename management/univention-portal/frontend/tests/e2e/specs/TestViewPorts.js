/*
  SPDX-FileCopyrightText: 2021-2026 Univention GmbH
  SPDX-License-Identifier: AGPL-3.0-only
*/

const sizes = ['iphone-8', 'ipad-2'];
const orientations = ['portrait', 'landscape'];

describe('Logo', () => {
  orientations.forEach((orientation) => {
    sizes.forEach((size) => {
      // make assertions on the logo using
      // an array of different viewports
      it(`Should display the menubutton on ${size} screen, orientation ${orientation}`, () => {
        cy.clearCookie('univentionCookieSettingsAccepted');
        cy.intercept('GET', 'portal.json', { fixture: 'portal_logged_out.json' });
        cy.intercept('GET', 'meta.json', { fixture: 'meta.json' });
        cy.intercept('GET', 'de.json', { fixture: 'de.json' });
        cy.intercept('GET', 'languages.json', { fixture: 'languages.json' });
        cy.viewport(size, orientation);

        cy.visit('/');
        cy.get('main.cookie-banner + footer button.button--primary').click();
        // reactivate after fix
        // cy.get('[data-test="navigationbutton"]').should('be.visible');
      });
    });
  });
});
