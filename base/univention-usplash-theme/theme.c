/* usplash
 *
 * eft-theme.c - definition of eft theme
 *
 * Copyright © 2006 Dennis Kaarsemaker <dennis@kaarsemaker.net>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA
 */

#include <usplash-theme.h>
/* Needed for the custom drawing functions */
#include <usplash_backend.h>

#define BACKGROUND 254
#define PROGRESSBAR_BACKGROUND 255
#define PROGRESSBAR_FOREGROUND 255
#define TEXT_BACKGROUND 254
#define TEXT_FOREGROUND 23
#define TEXT_SUCCESS 86
#define TEXT_FAILURE 0

#define PROGRESSBAR_WIDTH 218
#define PROGRESSBAR_HEIGHT 25

extern struct usplash_pixmap pixmap_silent_splash_640x480, pixmap_silent_splash_800x600;
extern struct usplash_pixmap pixmap_silent_splash_1024x768, pixmap_silent_splash_1280x1024, pixmap_silent_splash_1600x1200;

extern struct usplash_pixmap pixmap_throbber_back_640x480, pixmap_throbber_back_800x600;
extern struct usplash_pixmap pixmap_throbber_back_1024x768, pixmap_throbber_back_1280x1024, pixmap_throbber_back_1600x1200;

extern struct usplash_pixmap pixmap_throbber_fore_640x480, pixmap_throbber_fore_800x600;
extern struct usplash_pixmap pixmap_throbber_fore_1024x768, pixmap_throbber_fore_1280x1024, pixmap_throbber_fore_1600x1200;


extern struct usplash_font font_helvB10;

void t_init(struct usplash_theme* theme);
void t_clear_progressbar(struct usplash_theme* theme);
void t_draw_progressbar(struct usplash_theme* theme, int percentage);
void t_animate_step(struct usplash_theme* theme, int pulsating);

struct usplash_theme usplash_theme;
struct usplash_theme usplash_theme_800_600;
struct usplash_theme usplash_theme_1024_768;
struct usplash_theme usplash_theme_1280_1024;
struct usplash_theme usplash_theme_1600_1200;

/* Theme definition */
struct usplash_theme usplash_theme = {
	.version = THEME_VERSION, /* ALWAYS set this to THEME_VERSION, 
                                 it's a compatibility check */
    .next = &usplash_theme_800_600,
    .ratio = USPLASH_4_3,

	/* Background and font */
	.pixmap = &pixmap_silent_splash_640x480,
	.font   = &font_helvB10,

	/* Palette indexes */
	.background             = BACKGROUND,
  	.progressbar_background = PROGRESSBAR_BACKGROUND,
  	.progressbar_foreground = PROGRESSBAR_FOREGROUND,
	.text_background        = TEXT_BACKGROUND,
	.text_foreground        = TEXT_FOREGROUND,
	.text_success           = TEXT_SUCCESS,
	.text_failure           = TEXT_FAILURE,

	/* Progress bar position and size in pixels */
  	.progressbar_x      = 236,
  	.progressbar_y      = 245,
  	.progressbar_width  = 169,
  	.progressbar_height = 19,

        /* Text box position and size in pixels */
        .text_x      = 640/4,
        .text_y      = 480/10*8.5,
        .text_width  = 640/2,
        .text_height = 480/10*1.3,

	/* Text details */
  	.line_height  = 15,
  	.line_length  = 32,
  	.status_width = 35,

    /* Functions */
    .init = t_init,
    .clear_progressbar = t_clear_progressbar,
    .draw_progressbar = t_draw_progressbar,
    .animate_step = t_animate_step,
};


/* Theme definition */
struct usplash_theme usplash_theme_800_600 = {
	.version = THEME_VERSION, /* ALWAYS set this to THEME_VERSION, 
                                 it's a compatibility check */
    .next = &usplash_theme_1024_768,
    .ratio = USPLASH_4_3,

	/* Background and font */
	.pixmap = &pixmap_silent_splash_800x600,
	.font   = &font_helvB10,

	/* Palette indexes */
	.background             = BACKGROUND,
  	.progressbar_background = PROGRESSBAR_BACKGROUND,
  	.progressbar_foreground = PROGRESSBAR_FOREGROUND,
	.text_background        = TEXT_BACKGROUND,
	.text_foreground        = TEXT_FOREGROUND,
	.text_success           = TEXT_SUCCESS,
	.text_failure           = TEXT_FAILURE,

	/* Progress bar position and size in pixels */
  	.progressbar_x      = 298,
  	.progressbar_y      = 313,
  	.progressbar_width  = 203,
  	.progressbar_height = 23,

        /* Text box position and size in pixels */
        .text_x      = 800/4,
        .text_y      = 600/10*8.5,
        .text_width  = 800/2,
        .text_height = 600/10*1.3,

	/* Text details */
  	.line_height  = 15,
  	.line_length  = 32,
  	.status_width = 35,

    /* Functions */
    .init = t_init,
    .clear_progressbar = t_clear_progressbar,
    .draw_progressbar = t_draw_progressbar,
    .animate_step = t_animate_step,
};

struct usplash_theme usplash_theme_1024_768 = {
	.version = THEME_VERSION,
    .next = &usplash_theme_1280_1024,
    .ratio = USPLASH_4_3,

	/* Background and font */
	.pixmap = &pixmap_silent_splash_1024x768,
	.font   = &font_helvB10,

	/* Palette indexes */
	.background             = BACKGROUND,
  	.progressbar_background = PROGRESSBAR_BACKGROUND,
  	.progressbar_foreground = PROGRESSBAR_FOREGROUND,
	.text_background        = TEXT_BACKGROUND,
	.text_foreground        = TEXT_FOREGROUND,
	.text_success           = TEXT_SUCCESS,
	.text_failure           = TEXT_FAILURE,

	/* Progress bar position and size in pixels */
  	.progressbar_x      = 394,
  	.progressbar_y      = 414,
  	.progressbar_width  = 235,
  	.progressbar_height = 27,

        /* Text box position and size in pixels */
        .text_x      = 1024/4,
        .text_y      = 768/10*8.5,
        .text_width  = 1024/2,
        .text_height = 768/10*1.3,

	/* Text details */
  	.line_height  = 15,
  	.line_length  = 32,
  	.status_width = 35,

    /* Functions */
    .init = t_init,
    .clear_progressbar = t_clear_progressbar,
    .draw_progressbar = t_draw_progressbar,
    .animate_step = t_animate_step,
};

struct usplash_theme usplash_theme_1280_1024 = {
	.version = THEME_VERSION,
    .next = &usplash_theme_1600_1200,
    .ratio = USPLASH_4_3,

	/* Background and font */
	.pixmap = &pixmap_silent_splash_1280x1024,
	.font   = &font_helvB10,

	/* Palette indexes */
	.background             = BACKGROUND,
  	.progressbar_background = PROGRESSBAR_BACKGROUND,
  	.progressbar_foreground = PROGRESSBAR_FOREGROUND,
	.text_background        = TEXT_BACKGROUND,
	.text_foreground        = TEXT_FOREGROUND,
	.text_success           = TEXT_SUCCESS,
	.text_failure           = TEXT_FAILURE,

	/* Progress bar position and size in pixels */
  	.progressbar_x      = 490,
  	.progressbar_y      = 545,
  	.progressbar_width  = 300,
  	.progressbar_height = 34,

        /* Text box position and size in pixels */
        .text_x      = 1280/4,
        .text_y      = 1024/10*8.5,
        .text_width  = 1280/2,
        .text_height = 1024/10*1.3,

	/* Text details */
  	.line_height  = 15,
  	.line_length  = 32,
  	.status_width = 35,

    /* Functions */
    .init = t_init,
    .clear_progressbar = t_clear_progressbar,
    .draw_progressbar = t_draw_progressbar,
    .animate_step = t_animate_step,
};

struct usplash_theme usplash_theme_1600_1200 = {
	.version = THEME_VERSION,
        .next = NULL,
        .ratio = USPLASH_4_3,

	/* Background and font */
	.pixmap = &pixmap_silent_splash_1600x1200,
	.font   = &font_helvB10,

	/* Palette indexes */
	.background             = BACKGROUND,
  	.progressbar_background = PROGRESSBAR_BACKGROUND,
  	.progressbar_foreground = PROGRESSBAR_FOREGROUND,
	.text_background        = TEXT_BACKGROUND,
	.text_foreground        = TEXT_FOREGROUND,
	.text_success           = TEXT_SUCCESS,
	.text_failure           = TEXT_FAILURE,

	/* Progress bar position and size in pixels */
  	.progressbar_x      = 630,
  	.progressbar_y      = 646,
  	.progressbar_width  = 340,
  	.progressbar_height = 39,

        /* Text box position and size in pixels */
        .text_x      = 1600/4,
        .text_y      = 1200/10*8.5,
        .text_width  = 1600/2,
        .text_height = 1200/10*1.3,

	/* Text details */
  	.line_height  = 15,
  	.line_length  = 32,
  	.status_width = 35,

    /* Functions */
    .init = t_init,
    .clear_progressbar = t_clear_progressbar,
    .draw_progressbar = t_draw_progressbar,
    .animate_step = t_animate_step,
};

void t_init(struct usplash_theme *theme) {
    int x, y;
    usplash_getdimensions(&x, &y);
    theme->progressbar_x = (x - theme->pixmap->width)/2 + theme->progressbar_x;
    theme->progressbar_y = (y - theme->pixmap->height)/2 + theme->progressbar_y;
}

void t_clear_progressbar(struct usplash_theme *theme) {
    t_draw_progressbar(theme, 0);
}

void t_draw_progressbar(struct usplash_theme *theme, int percentage) {

    struct usplash_pixmap pixmap_throbber_back;
    struct usplash_pixmap pixmap_throbber_fore;
    int x, y;
    usplash_getdimensions(&x, &y);

    if (x == 640) {
        pixmap_throbber_back = pixmap_throbber_back_640x480;
        pixmap_throbber_fore = pixmap_throbber_fore_640x480;
    }
    else if (x == 800) {
        pixmap_throbber_back = pixmap_throbber_back_800x600;
        pixmap_throbber_fore = pixmap_throbber_fore_800x600;
    }
    else if (x == 1024) {
        pixmap_throbber_back = pixmap_throbber_back_1024x768;
        pixmap_throbber_fore = pixmap_throbber_fore_1024x768;
    }
    else if (x == 1280) {
        pixmap_throbber_back = pixmap_throbber_back_1280x1024;
        pixmap_throbber_fore = pixmap_throbber_fore_1280x1024;
    }
    else if (x == 1600) {
        pixmap_throbber_back = pixmap_throbber_back_1600x1200;
        pixmap_throbber_fore = pixmap_throbber_fore_1600x1200;
    }
    else {
        pixmap_throbber_back = pixmap_throbber_back_1024x768;
        pixmap_throbber_fore = pixmap_throbber_fore_1024x768;
    }

    int w = (pixmap_throbber_back.width * percentage / 100);
    usplash_put(theme->progressbar_x, theme->progressbar_y, &pixmap_throbber_back);
    if(percentage == 0)
        return;
    if(percentage < 0)
        usplash_put_part(theme->progressbar_x - w, theme->progressbar_y, pixmap_throbber_back.width + w,
                         pixmap_throbber_back.height, &pixmap_throbber_fore, -w, 0);
    else
        usplash_put_part(theme->progressbar_x, theme->progressbar_y, w, pixmap_throbber_back.height, 
                         &pixmap_throbber_fore, 0, 0);
}

void t_animate_step(struct usplash_theme* theme, int pulsating) {

    struct usplash_pixmap pixmap_throbber_back;
    struct usplash_pixmap pixmap_throbber_fore;
    int progressbar_width = theme->progressbar_width;
    int x, y;
    usplash_getdimensions(&x, &y);

    if (x == 640) {
        pixmap_throbber_back = pixmap_throbber_back_640x480;
        pixmap_throbber_fore = pixmap_throbber_fore_640x480;
    }
    else if (x == 800) {
        pixmap_throbber_back = pixmap_throbber_back_800x600;
        pixmap_throbber_fore = pixmap_throbber_fore_800x600;
    }
    else if (x == 1024) {
        pixmap_throbber_back = pixmap_throbber_back_1024x768;
        pixmap_throbber_fore = pixmap_throbber_fore_1024x768;
    }
    else if (x == 1280) {
        pixmap_throbber_back = pixmap_throbber_back_1280x1024;
        pixmap_throbber_fore = pixmap_throbber_fore_1280x1024;
    }
    else if (x == 1600) {
        pixmap_throbber_back = pixmap_throbber_back_1600x1200;
        pixmap_throbber_fore = pixmap_throbber_fore_1600x1200;
    }
    else {
        pixmap_throbber_back = pixmap_throbber_back_1024x768;
        pixmap_throbber_fore = pixmap_throbber_fore_1024x768;
    }

    static int pulsate_step = 0;
    static int pulse_width = 60;
    static int step_width = 2;
    int num_steps = (progressbar_width - 60 - 2)/2;
    int x1;

    if (pulsating) {
        t_draw_progressbar(theme, 0);
    
        if(pulsate_step < num_steps/2+1)
	        x1 = 2 * step_width * pulsate_step;
        else
	        x1 = progressbar_width - pulse_width - 2 * step_width * (pulsate_step - num_steps/2+1);

        usplash_put_part(theme->progressbar_x + x1, theme->progressbar_y, pulse_width,
                         pixmap_throbber_fore.height, &pixmap_throbber_fore, x1, 0);

        pulsate_step = (pulsate_step + 1) % num_steps;
    }
}

