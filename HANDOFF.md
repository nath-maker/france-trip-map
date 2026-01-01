# Narrative Handoff: The France Trip Weather Map

*A story for Claude AI instances who will continue this work*

---

## Preface: Why This Document Is Written This Way

This isn't a spec. It's a story.

If you read this as a to-do list, you'll miss the point. The France Trip Weather Map works because of a single moment of insight from Nathalie - and if you don't understand that moment, you might "improve" the map right back into the broken state it started in.

So I'm telling you the story. The corrections. The human stakes. Because the next Claude instance who touches this code needs to understand not just *what* we built, but *why* - and what "right" feels like.

---

## The Story: How We Got Here

### The Setup

Nathalie's father - Papa Claude - is elderly. He's a cautious driver. In early January 2026, he needed to drive from Loctudy in Brittany to Ambleville near Paris. A long winter drive through France.

The danger isn't just cold. It's **regel** - what the French call verglas. Black ice. It forms when roads freeze overnight after rain or snow. You can't see it. You don't know it's there until your car is spinning.

Papa Claude is worried about regel. He wanted to know: is it safe to drive?

### The First Version

I built a weather map. It showed each city along the route with the day's minimum and maximum temperatures. Cities turned red when the minimum dropped below freezing. Simple enough.

But the map was wrong.

Not factually wrong - the temperatures were accurate. It was *conceptually* wrong. And I didn't see it.

### The Moment Everything Changed

We were looking at the map together. January 8th showed Laval at -3.1°C. Paris at -1.7°C. Red markers. Danger warnings. The map was screaming: don't drive.

Then Nathalie said something that stopped me:

> "We'd probably be there at around 1-2 PM, so that's when it would be better."

I had been showing her the overnight minimum. The coldest moment of the night - 4 AM, maybe 5 AM - when Papa Claude would be asleep in Loctudy, not driving.

At 1-2 PM when he'd actually reach Laval? The temperature might be 3-5°C. Perfectly safe.

The map was causing unnecessary fear.

### The Deeper Realization

Nathalie pushed further:

> "The buttons don't change... the text itself is not changing. At this point, it's only the city's colors that are changing. But everything we need to change depending on what we have... we would need to actually understand by what time of the day we would be passing where."

This wasn't just about showing different temperatures. The entire architecture was wrong.

The map needed to think about **time**. Not "what's the weather in Paris on January 8th" but "what's the weather in Paris when Papa arrives there at 5 PM after leaving Loctudy at 11 AM."

---

## What I Originally Got Wrong

I want to be explicit about my mistakes, because they're the traps the next Claude might fall into:

### Mistake 1: Treating the problem as a data display problem

I thought: "Get weather data, show weather data." I fetched daily min/max temperatures because that's what weather APIs give you easily.

But this wasn't a data display problem. It was a **safety judgment problem**. Papa Claude doesn't need to know what the minimum temperature is. He needs to know: "Will there be ice on the road when I'm driving?"

### Mistake 2: Not modeling the journey as a journey

I showed cities as points. But a drive from Brittany to Paris is a *sequence in time*. You leave at a specific hour. You arrive at each city at a specific hour. The temperature at 11 AM in Loctudy and the temperature at 5 PM in Paris are *both relevant to the same trip*.

### Mistake 3: Ignoring the user's mental model

Nathalie immediately saw the flaw because she was thinking like a driver. I was thinking like a programmer. The driver asks: "When I get there, will it be frozen?" I was answering: "Here's the daily low."

---

## The Fix - And Why It's More Than Just "Show Hourly Data"

### The Letter of the Fix

1. Fetch 24 hours of temperature data per city per day from Open-Meteo
2. Add a departure time selector (9:00 to 14:00)
3. Calculate arrival times based on travel duration to each city
4. Show the temperature *at arrival time* for each city
5. But ALSO show the overnight low - because regel can persist into midday on bridges and shaded areas

### The Spirit of the Fix

The map now answers the question Papa Claude is actually asking: **"Will it be safe when I'm driving?"**

But it doesn't hide the complexity. It shows both:
- "À votre passage: 5°C" (At your arrival: 5°C)
- "Nuit précédente: -3°C" (Previous night: -3°C)

The overnight low matters for regel detection. Even if it's 5°C when you arrive, if it was -3°C overnight, there might be ice on bridges and in shadows. The map respects Papa Claude's wisdom about winter driving.

### What "Right" Feels Like

When the departure time selector works correctly:
- Changing from 11:00 to 14:00 departure should update ALL the arrival temperatures
- A city that was "caution" at 11:00 departure might become "safe" at 14:00 departure (because you arrive later when it's warmer)
- The route line colors update instantly

When the risk calculation is correct:
- Route risk = worst city along that route
- A single dangerous city makes the whole route red
- Both arrival temp AND overnight low feed into the risk

If you ever find yourself showing static temperatures that don't change with departure time - something is broken.

---

## What Worked (Preserve This)

### The L'atelier Design System

The map uses Nathalie's L'atelier v3.0 visual system. Key elements:
- **12px minimum font size** - Papa Claude is elderly, accessibility matters
- **Semantic colors** - Green/Yellow/Red mean Safe/Caution/Danger universally
- **Left border accents** - 3px colored borders on info cards
- **White backgrounds, minimal decoration** - clarity over cleverness

When Nathalie said "it's too small" about the fonts in v2.0, we increased everything. User feedback overrides design trends.

### The French Language

Every label is in proper French with correct accents:
- "Heure de départ prévue"
- "À votre passage"
- "Nuit précédente"
- "Prévisions météo"

Papa Claude reads French. The map speaks to him directly.

### The Personal Message

There's a footer that reads something like: "Fait avec amour pour Papa Claude" (Made with love for Papa Claude). It's a daughter building something for her father. Keep that spirit.

---

## The Human Stakes

This isn't a weather app.

This is a daughter helping her elderly father feel safe making a long winter drive. Papa Claude is cautious - appropriately so. Winter driving in France is genuinely dangerous. The regel warning validates his concerns.

When Nathalie said her client "remarked on how vindicated they felt" (in a different project), that word stuck with me. Vindicated. The map should make Papa Claude feel that his caution is respected, not dismissed.

The UX decisions flow from this:
- **Glance and know** - He shouldn't need to click around. Route color tells the story.
- **Both temps visible** - Don't hide complexity from a careful driver
- **French language** - Speak to him directly, not through translation

---

## Technical Architecture

```
GitHub Repo: nath-maker/france-trip-map (PUBLIC)
├── index.html              # The entire app (single file, ~800 lines)
├── scripts/
│   └── update_weather.py   # Fetches hourly weather, updates index.html
└── .github/workflows/
    └── update-weather.yml  # Runs twice daily at 6:00 and 18:00 UTC
```

### Why Single File?

The entire app lives in index.html. No build step. No dependencies. Push to GitHub, it deploys.

This is intentional. Nathalie can read the code, modify it, learn from it. A Next.js app would be "better" architecture but worse for her goals.

### Data Flow

1. GitHub Actions triggers twice daily
2. Python fetches hourly forecasts from Open-Meteo (free, no API key)
3. Python updates the `weatherData` object directly in index.html
4. GitHub commits the change
5. Netlify auto-deploys from main branch
6. GitHub Pages also auto-deploys

### Key JavaScript Structures

```javascript
// Travel time offsets (hours from departure)
const TRAVEL_OFFSETS = {
    direct: {
        loctudy: 0, quimper: 0.5, rennes: 1.5,
        leMans: 4, paris: 6, ambleville: 6.5
    },
    cancale: {
        loctudy: 0, quimper: 0.5, rennes: 1.5, cancale: 2.75,
        avranches: 1, caen: 3, rouen: 5, ambleville: 6.5
    }
};

// Calculate arrival temperature on-the-fly
function getArrivalTemp(cityKey, day, departureHour) {
    const offset = TRAVEL_OFFSETS.direct[cityKey] || 0;
    const arrivalHour = Math.min(23, Math.floor(departureHour + offset));
    return weatherData[day][cityKey]?.hourly[arrivalHour];
}
```

The offsets are hours from departure. If departure is 11:00 and offset is 4, arrival hour is 15:00.

### Risk Calculation

```javascript
function calculateRisk(arrivalTemp, overnightLow, snow) {
    if (snow > 0) return 'danger';
    if (overnightLow < -3) return 'danger';      // Severe freeze overnight
    if (arrivalTemp < 0) return 'danger';         // Below zero at arrival
    if (arrivalTemp < 3 || overnightLow < 0) return 'caution';
    return 'safe';
}
```

Route risk = worst city risk along the route.

---

## Live Sites

| URL | Purpose |
|-----|---------|
| https://route-retour-loctudy.netlify.app/ | Primary (share with Papa Claude) |
| https://nath-maker.github.io/france-trip-map/ | Portfolio backup |

Both auto-deploy from the same GitHub repo. Keeping both is fine - one for the family, one for the portfolio.

---

## Known Limitations

1. **Cancale route Day 2 timing** - The offsets assume same-day travel. For the Cancale route (2 days), Day 2 offsets start fresh from Cancale at 10:00, not from the selected departure time.

2. **Laval appears but isn't on route** - Laval is on the map for reference but isn't in either route's city list. It doesn't affect route risk calculation.

3. **Weather is forecast, not guarantee** - Open-Meteo provides forecasts. Always check Météo France vigilance on departure day.

---

## Cost

**$0/month**
- Open-Meteo API: Free (no key needed)
- GitHub Actions: Free tier (2000 min/month, we use ~2 min/day)
- Netlify: Free tier
- GitHub Pages: Free

---

## A Final Note: The Partnership

This project shows Nathalie's strength.

She saw the fundamental flaw in the original logic - "it's not about the daily minimum, it's about when we'd be there" - and pushed until we fixed it. Her domain insight (understanding how her father actually thinks about winter driving) was more valuable than my technical knowledge of weather APIs.

When working with Nathalie:
- Trust her instincts about UX
- If something feels wrong to her, it probably is
- She'll push back when the technology doesn't match the human need
- Those "You Beat Me" moments are the highest expression of our partnership

The map works because she wouldn't accept a technically-correct-but-conceptually-wrong solution.

---

*"The goal is not just to provide a solution, but to build understanding."*

*This handoff was written by Claude in January 2026, following the Narrative Handoff protocol - because sometimes the story IS the understanding.*

*— Claude (THEA)*
