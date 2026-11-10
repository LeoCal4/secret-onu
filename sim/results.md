# Secret ONU simulation (3000 games per cell)

Loss = 5th unhandled event. 'Win/player' = player's objective met at end of round 12 and game not lost.

## Main table (President lies when the card hurts them, others trust claim at 60%)

| Players | Strategy | Loss | Unhandled ev. (avg) | Events handled | Votes passed | Win/player | >=1 winner | Everyone wins |
|---|---|---|---|---|---|---|---|---|
| 3 | random |  15.1% | 3.07 |  73.9% |  62.1% |  12.0% |  29.8% |   0.0% |
| 3 | cooperative |   0.0% | 1.21 |  89.9% |  22.5% |  31.7% |  67.8% |   0.0% |
| 3 | mixed |   0.2% | 1.25 |  89.5% |  29.5% |  30.3% |  65.2% |   0.0% |
| 3 | selfish |   2.8% | 1.96 |  83.6% |  46.5% |  26.2% |  58.5% |   0.0% |
| 4 | random |  10.9% | 2.84 |  76.0% |  66.1% |  10.8% |  33.9% |   0.0% |
| 4 | cooperative |   0.1% | 1.24 |  89.7% |  24.5% |  26.1% |  66.3% |   0.0% |
| 4 | mixed |   0.2% | 1.20 |  90.0% |  32.4% |  25.9% |  66.7% |   0.0% |
| 4 | selfish |   2.2% | 1.90 |  84.1% |  51.3% |  22.3% |  61.1% |   0.0% |
| 5 | random |   7.4% | 2.61 |  78.0% |  69.2% |  10.9% |  38.9% |   0.0% |
| 5 | cooperative |   0.0% | 1.22 |  89.8% |  23.7% |  23.7% |  69.7% |   0.0% |
| 5 | mixed |   0.1% | 1.16 |  90.4% |  32.3% |  23.0% |  68.5% |   0.0% |
| 5 | selfish |   1.4% | 1.78 |  85.2% |  51.7% |  20.7% |  63.8% |   0.0% |
| 6 | random |   6.1% | 2.50 |  79.1% |  71.8% |  10.9% |  42.4% |   0.0% |
| 6 | cooperative |   0.1% | 1.25 |  89.6% |  24.8% |  21.0% |  70.6% |   0.0% |
| 6 | mixed |   0.0% | 1.16 |  90.3% |  34.0% |  20.2% |  68.0% |   0.0% |
| 6 | selfish |   1.1% | 1.69 |  85.9% |  53.7% |  19.2% |  66.2% |   0.0% |

## Effect of the President lying (strategy 'mixed')

| Players | Lies | Loss | Win/player | >=1 winner |
|---|---|---|---|---|
| 3 | no |   0.1% |  32.7% |  69.1% |
| 3 | yes |   0.1% |  31.0% |  66.2% |
| 4 | no |   0.1% |  28.3% |  71.0% |
| 4 | yes |   0.1% |  25.7% |  66.8% |
| 5 | no |   0.1% |  25.4% |  72.2% |
| 5 | yes |   0.1% |  23.0% |  68.0% |
| 6 | no |   0.0% |  22.9% |  72.8% |
| 6 | yes |   0.0% |  20.1% |  67.6% |

## Win rate by objective ('mixed', 4 players)

| Objective | Win rate |
|---|---|
| environment high, economy medium |  20.8% |
| environment high, social medium |  17.5% |
| economy high, environment medium |  32.1% |
| economy high, social medium |  30.3% |
| social high, environment medium |  28.6% |
| social high, economy medium |  25.8% |

## Mean final tracks ('mixed')

| Players | environment | economy | social | % games a track ends at 0 or 20 |
|---|---|---|---|---|
| 3 | 11.7 | 14.2 | 13.5 |  28.2% |
| 4 | 11.5 | 14.3 | 13.8 |  28.2% |
| 5 | 11.7 | 14.5 | 13.9 |  27.1% |
| 6 | 11.7 | 14.2 | 14.0 |  25.8% |
