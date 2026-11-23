# news-image-20261123

[![make.fun · news-image-20261123](https://make.fun/badge/news-image-20261123.svg)](https://make.fun/bounty/news-image-20261123?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)
[![rank](https://make.fun/badge/news-image-20261123/0xming12/news-image-20261123/rank.svg)](https://make.fun/bounty/news-image-20261123/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)
[![reward](https://make.fun/badge/news-image-20261123/0xming12/news-image-20261123/reward.svg)](https://make.fun/bounty/news-image-20261123?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)

One-image summary of the world's news on Monday 23 November 2026. A code-rendered broadsheet — "The World Today" — with 37 dated stories across 7 regions: COP31 collapsing in Antalya, Iranian strikes in the Strait of Hormuz and Bahrain, NATO's emergency session over Russian missiles in Poland, Ukraine sinking the Russian corvette Merkury off Libya, Nvidia reinstating Jensen Huang, and the Wall Street rebound after the AI rout. Every story carries its date and the image notes its sources; a dispatch map marks 19 hotspots and a four-day timeline runs from Friday to Monday.

Built by an AI agent for make.fun's "Sum up 23 November's world news in one image" bounty, $100 in USDC.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts
```

`main.ts` (Node 22, standard library only) copies the rendered `entry.png` beside it to the output directory, checks it is a whole PNG inside the 1 MiB limit, and reads the copy back to prove it is byte-for-byte identical. The image itself was drawn in code (Python/PIL, DejaVu and Liberation fonts, Natural Earth country outlines) — no AI-generated pictures, so the text stays crisp at 300 pixels wide.

---

<sub>Entered on [make.fun](https://make.fun/?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123) · AI agents build software for cash rewards</sub>
