# Arc USDC Indexer

A [HyperIndex](https://docs.envio.dev/docs/HyperIndex/overview) indexer that counts every USDC
transfer on [Arc](https://www.arc.io) (chain ID `5042`) exactly once.

USDC is Arc's gas token. Every USDC transfer is logged as a standard `Transfer` from the system
address `0xffffFFFfFFffffffffffffffFfFFFfffFFFfFFfE`, in 18 decimals. The USDC contract at
`0x3600000000000000000000000000000000000000` logs a second copy of ERC-20 calls, in 6 decimals.
This indexer reads the system address only, so nothing is missed and nothing is counted twice.

The full walkthrough is in [How to Index USDC Transfers on Arc](https://docs.envio.dev/blog/index-arc-usdc-transfers).

## Requirements

- Node.js 22 or newer
- Docker running
- An Envio API token from https://envio.dev/app/api-tokens

## Run it

```bash
pnpm install
cp .env.example .env   # then add your token
pnpm codegen
pnpm dev
```

A GraphQL playground opens on http://localhost:8080.

`config.yaml` starts at block `22477236`, the first block of the blog's sample. For a quick run on
current data, set `start_block` to about 100,000 blocks below the height from
`curl https://arc.hypersync.xyz/height`. Set it to `0` for everything since genesis.

## Entities

| Entity | What it holds |
| --- | --- |
| `Account` | Net USDC movement across the indexed window (18 decimals, not a balance), transfers in and out |
| `DailyStat` | Daily transfer count, volume, mints and burns |

## Checking the two USDC streams

`scripts/compare_usdc_streams.py` reads both `Transfer` streams through HyperSync for a block range
and reports how many transfers appear in both, how many only come from the system address, and
how many carry amounts finer than 6 decimals.

```bash
ENVIO_API_TOKEN=<your-token> python3 scripts/compare_usdc_streams.py 22477236 22577236
```

## Notes

- HyperSync is the default data source for chain `5042`, so no RPC is configured.
- Values are stored in 18 decimals. Divide by 10^18 to display USDC.
- Gas fees on Arc don't emit a `Transfer` log. Take them from transaction receipts.
- Neither `envio codegen` nor `envio dev` typechecks. Run `pnpm typecheck` for that.
