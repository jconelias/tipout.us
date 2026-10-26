# TipOut App Store creative (made 2026-10-26, v1.5.6 launch)

All art uses real TipOut screens pulled from Jordan's Oct 7 iPhone screen recordings (status bar cleaned to 9:41). No alpha channel, no prices, no URLs, per Apple's rules.

## Header and Search Results (App Store Connect > Product Page Information > Header / Search Results, or Asset Library)
| File | Placement | Size |
|---|---|---|
| header-and-search/TipOut-header-21x9_3840x1646.png (.jpg) | Product page header, 21:9 | 3840 x 1646 |
| header-and-search/TipOut-search-results-3x2_3840x2560.png (.jpg) | Search results, 3:2 | 3840 x 2560 |
| header-and-search/TipOut-universal-16x9_5244x2950.png | Universal (one image for both, Apple crops it) | 5244 x 2950 |

Use the header + search results pair (best control). The universal file is a fallback if you only want to upload one. Check both with the Preview button before submitting; Apple reviews each asset.

## iPhone screenshots (upload in this order)
1. Snap it. Shift logged. (Snap your checkout)
2. Your whole year, at a glance. (See your year)
3. Find your best nights. (Best nights + tip rate)
4. Know what your shifts are worth. (Real hourly)
5. Split the tip pool to the cent. (Bar split)
6. Tax time? Already done. (CSV export)

Folders: 6.9in-1320x2868 (main, required class), 6.5in-1284x2778, 6.3in-1206x2622. Uploading the 6.9" set alone is enough; App Store Connect scales it down for smaller iPhones.

## iPhone Duo (foldable) screenshots
Same 6 screens laid out for the wider Duo canvas: screenshots/duo-2007x2853 (inner display) and screenshots/duo-1398x2034 (outer display). Apple will require Duo screenshots from April 2027.

## Rebuild
_build/clean.py (status bar), _build/make.py (HTML layouts), _build/render.js (Playwright render). Fonts: launch/_build/N7-9.ttf in ~/.fonts.
