# Objective pool (12) and preset sets per player count (DRAFT)

Every objective names two tracks: one target section for each (high / medium / low).
The simulator does not read this file yet; `test_objectives.md` is unchanged.

## Pool

Each track is the main goal ("high") in 4 objectives, and is the side condition in 4 others (2 medium, 2 low).

| # | Name | Environment | Economy | Social | Rationale |
|---|---|---|---|---|---|
| 1 | Green Transition | high | medium | - | Decarbonise without wrecking the economy |
| 2 | Welfare State | - | medium | high | Strong public services, steady economy |
| 3 | Growth Power | medium | high | - | Expand the economy, keep the environment stable |
| 4 | Free Market | - | high | medium | Open markets, no social upheaval |
| 5 | Conservation | high | - | medium | Protect nature without social turmoil |
| 6 | Humanist | medium | - | high | Rights first, steady environment |
| 7 | Degrowth | high | low | - | Shrink the economy to protect the planet |
| 8 | Resource Power | low | high | - | Extract and export, accept the environmental cost |
| 9 | Efficient State | - | high | low | Prosperity through order, rights come second |
| 10 | Solidarity Economy | - | low | high | Post-growth society built on rights and sharing |
| 11 | Right to Development | low | - | high | Rights and industrialisation before climate |
| 12 | Fortress Conservation | high | - | low | Protect nature by restricting people |

Facts about the pool:
- Every objective is compatible (can be won together) with exactly 3 others.
- No three objectives are mutually compatible, so at most 2 players can ever win in the same game, whatever the player count.
- Compatible pairs: 1-2, 1-5, 1-12, 2-6, 2-11, 3-4, 3-6, 3-9, 4-5, 4-8, 5-7, 6-10, 7-10, 7-12, 8-9, 8-11, 9-12, 10-11.

## Presets

"Allies" are pairs that can win together. A player with a low objective is usually the one who benefits from events going unhandled.

### 3 players
- **3-A "The spoiler wants growth":** 1 Green Transition, 2 Welfare State, 8 Resource Power
  - Allies: 1+2. Resource Power opposes both. One low objective.
- **3-B "The spoiler wants degrowth":** 3 Growth Power, 6 Humanist, 7 Degrowth
  - Allies: 3+6. Degrowth opposes both. One low objective.

### 4 players
- **4-A "Sustainable vs growth":** 1 Green Transition, 2 Welfare State, 3 Growth Power, 9 Efficient State
  - Two blocs of two: 1+2 and 3+9. They fight over the economy (medium vs high). One low objective.
- **4-B "Degrowth vs growth":** 7 Degrowth, 10 Solidarity Economy, 3 Growth Power, 4 Free Market
  - Two blocs: 7+10 and 3+4, opposite on the economy. Two low objectives, both on economy. The most polarised draft.

### 5 players
- **5-A "The kingmaker":** 1 Green Transition, 2 Welfare State, 3 Growth Power, 9 Efficient State, 11 Right to Development
  - Allies: 1+2, 2+11, 3+9. Welfare State can pair with either of two players who conflict with each other. Two low objectives.
- **5-B "The chain":** 8 Resource Power, 4 Free Market, 5 Conservation, 7 Degrowth, 10 Solidarity Economy
  - Allies chain: 8+4, 4+5, 5+7, 7+10. The two ends are opposites. Three low objectives, so the most suspicion.

### 6 players
- **6-A "Even bounce":** 1 Green Transition, 2 Welfare State, 3 Growth Power, 4 Free Market, 11 Right to Development, 12 Fortress Conservation
  - Allies: 1+2, 1+12, 2+11, 3+4. Each track is the main goal of exactly 2 players. Two low objectives.
- **6-B "Three blocs":** 4 Free Market, 5 Conservation, 6 Humanist, 9 Efficient State, 10 Solidarity Economy, 12 Fortress Conservation
  - Allies: 4+5, 6+10, 9+12. Three separate pairs compete. Three low objectives. Each track is the main goal of exactly 2 players.

## Summary

| Set | Low objectives | Compatible pairs | Main goal per track (env / econ / soc) |
|---|---|---|---|
| 3-A | 1 | 1 | 1 / 1 / 1 |
| 3-B | 1 | 1 | 1 / 1 / 1 |
| 4-A | 1 | 2 | 1 / 2 / 1 |
| 4-B | 2 | 2 | 1 / 2 / 1 |
| 5-A | 2 | 3 | 1 / 2 / 2 |
| 5-B | 3 | 4 | 2 / 2 / 1 |
| 6-A | 2 | 4 | 2 / 2 / 2 |
| 6-B | 3 | 3 | 2 / 2 / 2 |

## Open points
- At most 2 players can win together, so at 6 players at most 2 of 6 can win. If that feels too low, some objectives could have a single condition (for example only "environment high"), which makes them compatible with more.
- How hard each objective is to reach depends on the quadrants. Until their drift is balanced, these sets can't be fairly compared.
