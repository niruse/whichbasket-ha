# Supermarket price compare for Home Assistant

🇮🇱 **[בעברית](README.he.md)**

Compares your shopping list across the supermarket branches you choose, and shows where the whole list costs least. The work is done by the website [whichbasket.com](https://whichbasket.com): it imports the chains' price files every night and computes the comparison. Home Assistant only sends it the list and shows the answer.

- **List:** keep a list of its own, or follow a to-do list you already have (such as Home Assistant's shopping list).
- **Sensors:** the cheapest branch, what the whole list costs there, how much you save against the most expensive branch, and what the list costs at each branch you chose.
- **Card:** search and add, the list with each chain's price, and a comparison table. You can correct in the card which of a chain's products matches an item.
- **Ready dashboards** for a phone, a tablet and the home screen.
- **Blueprint:** a phone notification at the time you choose, with the branch where the whole list is cheapest today.

Prices are shelf prices from the chains' price transparency files, without deals. The price that counts is the one at the till or on the chain's site. **Before paying, check the cart on the chain's site: checking it is your responsibility.**

Currently covers Israeli supermarket chains.

## What is sent to the site

Only the branches you chose, the list's items (a product code, or the text you typed) and their quantities, and the searches you make in the card. When you choose another product for a chain in the card, the choice is also sent to the site as a suggestion for its admin, and applies to everyone only after the admin approves it. No sign-up and no key. The site keeps nothing about you: [privacy policy](https://whichbasket.com/privacy).

## Installation

Requires Home Assistant 2025.1 or later.

**With HACS (recommended):**

[![Open in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=niruse&repository=whichbasket-ha&category=integration)

Or by hand:

1. In HACS, choose ⋮ and then "Custom repositories".
2. Paste `https://github.com/niruse/whichbasket-ha`, choose the type Integration, and click Add.
3. Search for "Supermarket price compare", download it, and restart Home Assistant.

**Manually:**

1. Download `shopping_compare_web.zip` from the site's [Home Assistant page](https://whichbasket.com/home-assistant).
2. Unzip it in Home Assistant's configuration folder (the one that holds `configuration.yaml`), so that `custom_components/shopping_compare_web` is there.
3. Restart Home Assistant.

## Setup

1. Go to Settings → Devices & services → Add integration, and search for "Supermarket price compare".
2. **Town:** type part of the town's name and choose it from the list.
3. **Branches:** up to 12. By default, the biggest branch of each chain in the town is chosen.
4. **List:** the integration's own list (`todo.supermarket_list`), or follow an existing to-do list. When following, what you add in the card goes into that list.

You can change the town, branches and list later with the integration's Configure button.

## Entities

| Entity | What it is |
|:--|:--|
| `sensor.supermarket_cheapest_branch` | The branch where the whole list is cheapest. Attributes: the total, how many items were found and missing, and a link to the cart on the chain's site. |
| `sensor.supermarket_cheapest_total` | What the whole list costs there (₪). |
| `sensor.supermarket_saving` | How much you save against the most expensive branch (₪). |
| `sensor.supermarket_branch_<number>` | What the list costs at each branch you chose. |
| `sensor.supermarket_list_items` | How many items are on the list. |
| `sensor.supermarket_prices_updated` | When the site last updated its prices. |
| `binary_sensor.supermarket_site` | Whether the site can be reached. Without it, the last comparison stays and the list keeps working. |
| `button.supermarket_compare_now` | Compare now. |
| `todo.supermarket_list` | The list (only when the integration keeps a list of its own). |

The comparison updates when the list changes, every 6 hours, and once a day in the morning after the site updates its prices.

## The card

The card loads by itself; there is no resource to add. To add it, edit a dashboard, choose "Add card", then "Manual":

```yaml
type: custom:shopping-compare-web-card
view: full        # full (list and comparison) | list | compare | summary
```

In the comparison table, the ✎ button in each cell lets you choose another product at that chain, or mark it "not sold". A product found only in another size (for example a pack of 8 instead of one) is marked ⚠ and left out of the total until you choose it.

## Dashboards

The files are in the [`dashboards`](dashboards) folder, and the top of each says how to add it:

- `shopping-compare.yaml`: a full dashboard with the list, where it's cheapest, the branches, a graph over time and a full comparison screen.
- `phone-view.yaml`: one screen for a phone.
- `tablet-view.yaml`: a screen for a tablet or wall display, with the list, the comparison and the branches side by side.
- `summary-card.yaml`: a small card for the main dashboard.

## Blueprint: where it's cheapest today

A notification to your phone on the days and at the time you choose. It is sent only when the list has enough items and the saving is worth it. Tapping it opens the cart on the chain's site, where possible.

[![Import the blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fwhichbasket.com%2Fhome-assistant%2Fcheapest_notify.yaml)

## Troubleshooting

- **"No connection to the site":** the site may be in the middle of its nightly update. The last comparison stays, and the next one tries again.
- **A product isn't found at a chain:** search for it with the ✎ button in the table and choose the chain's product.
- **"Another size":** the chain sells the product in another size. Choose the right product with the ✎ button, or leave it out of the total.

## Ideas, issues and contributing

[Suggest an idea](https://whichbasket.com/ideas) on the site, or [open an issue](https://github.com/niruse/whichbasket-ha/issues) here.

## License

MIT
