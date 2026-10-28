# השוואת מחירים לסופר ל-Home Assistant

**[English below](#supermarket-price-compare-for-home-assistant)**

האינטגרציה משווה את רשימת הקניות שלכם בסניפים שתבחרו, ומראה איפה כל הרשימה הכי זולה. העבודה נעשית באתר [shopping-compare.onrender.com](https://shopping-compare.onrender.com): האתר מייבא כל לילה את קבצי המחירים של הרשתות ומחשב את ההשוואה. Home Assistant רק שולח לאתר את הרשימה ומציג את התשובה.

- **רשימה:** אפשר לנהל רשימה משלה, או לעקוב אחרי רשימת מטלות שכבר יש לכם (למשל רשימת הקניות של Home Assistant).
- **חיישנים:** הסניף הזול, כמה עולה בו כל הרשימה, כמה חוסכים מול הסניף היקר, וכמה עולה הרשימה בכל סניף שבחרתם.
- **כרטיס:** חיפוש והוספה, הרשימה עם המחירים בכל רשת, וטבלת השוואה. אפשר לתקן בכרטיס איזה מוצר של רשת מתאים לפריט.
- **דשבורדים מוכנים** לטלפון, לטאבלט ולמסך הבית.
- **Blueprint:** התראה לטלפון בשעה שתבחרו, עם הסניף שבו כל הרשימה הכי זולה היום.

המחירים הם מחירי מדף מקבצי השקיפות, בלי מבצעים. המחיר הקובע הוא בקופה או באתר הרשת. **לפני התשלום בדקו את העגלה באתר הרשת: האחריות לבדיקה היא שלכם.**

## מה נשלח לאתר

נשלחים רק הסניפים שבחרתם, פריטי הרשימה (קוד המוצר, או הטקסט שהקלדתם) והכמויות, וחיפושים שאתם עושים בכרטיס. כשאתם בוחרים בכרטיס מוצר אחר לרשת מסוימת, הבחירה נשלחת לאתר גם כהצעה למנהל האתר, ותחול על כולם רק אחרי שיאשר אותה. אין הרשמה ואין מפתח. האתר לא שומר עליכם כלום: [מדיניות הפרטיות](https://shopping-compare.onrender.com/privacy).

## התקנה

צריך Home Assistant בגרסה 2025.1 ומעלה.

**התקנה ידנית:**

1. מורידים את הקובץ `shopping_compare_web.zip` מעמוד [Home Assistant באתר](https://shopping-compare.onrender.com/home-assistant).
2. פותחים אותו בתיקיית ההגדרות של Home Assistant (התיקייה שבה נמצא `configuration.yaml`). אחרי הפתיחה צריכה להיות שם התיקייה `custom_components/shopping_compare_web`.
3. מפעילים מחדש את Home Assistant.

**דרך HACS:**

[![פתיחה ב-HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=niruse&repository=whichbasket-ha&category=integration)

או ידנית:

1. ב-HACS בוחרים ⋮ ואז "Custom repositories".
2. מדביקים את `https://github.com/niruse/whichbasket-ha`, בוחרים בסוג Integration ולוחצים Add.
3. מחפשים "Supermarket price compare", מתקינים ומפעילים מחדש.

## הגדרה

1. בהגדרות בוחרים "מכשירים ושירותים", ואז "הוספת אינטגרציה". מחפשים "Supermarket price compare".
2. **עיר:** כותבים חלק משם העיר ובוחרים אותה מהרשימה.
3. **סניפים:** עד 12. כברירת מחדל נבחר הסניף הגדול של כל רשת בעיר.
4. **רשימה:** רשימה של האינטגרציה עצמה (`todo.supermarket_list`), או מעקב אחרי רשימת מטלות קיימת. במעקב, מה שתוסיפו בכרטיס נכנס לרשימה הקיימת.

אחר כך אפשר לשנות עיר, סניפים ורשימה בכפתור "הגדרות" של האינטגרציה.

## מה נוצר

| ישות | מה זה |
|:--|:--|
| `sensor.supermarket_cheapest_branch` | הסניף שבו כל הרשימה הכי זולה. במאפיינים: הסכום, כמה נמצאו, כמה חסרים, וקישור לעגלה באתר הרשת. |
| `sensor.supermarket_cheapest_total` | כמה עולה כל הרשימה שם (₪). |
| `sensor.supermarket_saving` | כמה חוסכים מול הסניף היקר (₪). |
| `sensor.supermarket_branch_<מספר>` | כמה עולה הרשימה בכל סניף שבחרתם. |
| `sensor.supermarket_list_items` | כמה פריטים ברשימה. |
| `sensor.supermarket_prices_updated` | מתי האתר עדכן את המחירים. |
| `binary_sensor.supermarket_site` | האם יש חיבור לאתר. בלי חיבור מוצגת ההשוואה האחרונה, והרשימה ממשיכה לעבוד. |
| `button.supermarket_compare_now` | השוואה עכשיו. |
| `todo.supermarket_list` | הרשימה (רק כשהאינטגרציה מנהלת רשימה משלה). |

ההשוואה מתעדכנת כשהרשימה משתנה, כל 6 שעות, ופעם ביום בבוקר אחרי שהאתר מעדכן מחירים.

## הכרטיס

הכרטיס נטען לבד, ואין צורך להוסיף משאב. כדי להוסיף אותו: עורכים דשבורד, בוחרים "הוספת כרטיס", ואז "ידני":

```yaml
type: custom:shopping-compare-web-card
view: full        # full (רשימה והשוואה) | list | compare | summary
```

בטבלת ההשוואה, הכפתור ✎ שבכל תא פותח בחירה של מוצר אחר באותה רשת, או סימון "לא נמכר". מוצר שנמצא רק בגודל אחר (למשל מארז 8 במקום יחידה אחת) מסומן ⚠ ולא נספר בסכום, עד שתבחרו בו.

## דשבורדים

הקבצים נמצאים בתיקייה [`dashboards`](dashboards), ובראש כל קובץ כתוב איך מוסיפים אותו:

- `shopping-compare.yaml`: דשבורד שלם, עם רשימה, איפה הכי זול, הסניפים, גרף לאורך זמן ומסך השוואה מלא.
- `phone-view.yaml`: מסך אחד לטלפון.
- `tablet-view.yaml`: מסך לטאבלט או למסך קיר, עם הרשימה, ההשוואה והסניפים זה לצד זה.
- `summary-card.yaml`: כרטיס קטן לדשבורד הראשי.

## Blueprint: איפה הכי זול היום

התראה לטלפון בימים ובשעה שתבחרו. היא נשלחת רק כשיש מספיק פריטים ברשימה, וכשהחיסכון שווה את זה. לחיצה על ההתראה פותחת את העגלה באתר הרשת, כשאפשר.

[![ייבוא ה-blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fshopping-compare.onrender.com%2Fhome-assistant%2Fcheapest_notify.yaml)

## אם משהו לא עובד

- **"אין חיבור לאתר":** האתר עשוי להיות באמצע עדכון הלילה. ההשוואה האחרונה נשארת, וההשוואה הבאה תנסה שוב.
- **מוצר לא נמצא ברשת:** אפשר לחפש אותו בכפתור ✎ שבטבלה, ולבחור את המוצר של הרשת.
- **"גודל אחר":** הרשת מוכרת את המוצר בגודל אחר. בחרו את המוצר הנכון בכפתור ✎, או השאירו אותו מחוץ לסכום.
- **רעיון או בקשה:** [רעיון לשיפור](https://shopping-compare.onrender.com/ideas).

---

# Supermarket price compare for Home Assistant

The integration compares your shopping list in the branches you choose and shows where the whole list costs least. The work is done by the website [shopping-compare.onrender.com](https://shopping-compare.onrender.com), which imports the chains' price files every night and computes the comparison; Home Assistant sends it the list and shows the answer.

- **List:** a list of its own, or follow a to-do list you already have (such as Home Assistant's shopping list).
- **Sensors:** the cheapest branch, what the whole list costs there, the saving against the dearest branch, and the list's cost in each chosen branch.
- **Card:** search and add, the list with each chain's price, and the comparison table. You can correct which product of a chain matches an item.
- **Ready dashboards** for a phone, a tablet and the home screen.
- **Blueprint:** a phone notification at the time you choose with today's cheapest branch.

Prices are shelf prices from the chains' transparency files, without deals; the till price, or the chain's site, is what counts. **Before paying, check the cart on the chain's site: checking it is your responsibility.**

**What is sent to the site:** the chosen branches, the list's items (a product code, or the text you typed), their amounts, and searches you make in the card. A product you choose for a chain in the card is also sent as a suggestion for the site's admin, and applies to everyone only once the admin approves it. No sign-up and no key. The site keeps nothing about you: [privacy policy](https://shopping-compare.onrender.com/privacy).

**Install:** Home Assistant 2025.1 or later.

- **Manually:** download `shopping_compare_web.zip` from the site's [Home Assistant page](https://shopping-compare.onrender.com/home-assistant), unzip it in your Home Assistant configuration folder (so that `custom_components/shopping_compare_web` is there), and restart.
- **With HACS:** [open it in HACS](https://my.home-assistant.io/redirect/hacs_repository/?owner=niruse&repository=whichbasket-ha&category=integration), or add `https://github.com/niruse/whichbasket-ha` under HACS → ⋮ → Custom repositories (type Integration); then install "Supermarket price compare" and restart.

**Set up:** go to Settings → Devices & services → Add integration → "Supermarket price compare", then:

1. Choose the town.
2. Choose up to 12 branches (by default, each chain's biggest branch there).
3. Choose the list: the integration's own (`todo.supermarket_list`), or one to follow.

To change any of these later, use the integration's Configure button.

**Card:** it loads by itself. To add it, use Add card → Manual:

```yaml
type: custom:shopping-compare-web-card
view: full        # full | list | compare | summary
```

**Dashboards:** see the [`dashboards`](dashboards) folder; each file says how to add it.

**Blueprint:**

[![Import the blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fshopping-compare.onrender.com%2Fhome-assistant%2Fcheapest_notify.yaml)

**Ideas and requests:** [suggest an idea](https://shopping-compare.onrender.com/ideas), or open an issue here.

License: MIT.
