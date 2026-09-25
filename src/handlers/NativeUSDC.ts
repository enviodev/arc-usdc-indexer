import { indexer } from "envio";

const ZERO = "0x0000000000000000000000000000000000000000";
const DAY = 86_400;

indexer.onEvent(
  { contract: "NativeUSDC", event: "Transfer" },
  async ({ event, context }) => {
    const { from, to, value } = event.params;
    const day = String(Math.floor(event.block.timestamp / DAY));

    // The system emitter skips self transfers, so from and to always differ.
    // Mints come from the zero address and burns go to it.
    const [sender, receiver, stat] = await Promise.all([
      from === ZERO ? undefined : context.Account.get(from),
      to === ZERO ? undefined : context.Account.get(to),
      context.DailyStat.getOrCreate({
        id: day,
        transfers: 0,
        volume: 0n,
        mints: 0,
        burns: 0,
      }),
    ]);

    if (from !== ZERO) {
      context.Account.set({
        id: from,
        netChange: (sender?.netChange ?? 0n) - value,
        transfersIn: sender?.transfersIn ?? 0,
        transfersOut: (sender?.transfersOut ?? 0) + 1,
      });
    }
    if (to !== ZERO) {
      context.Account.set({
        id: to,
        netChange: (receiver?.netChange ?? 0n) + value,
        transfersIn: (receiver?.transfersIn ?? 0) + 1,
        transfersOut: receiver?.transfersOut ?? 0,
      });
    }

    context.DailyStat.set({
      ...stat,
      transfers: stat.transfers + 1,
      volume: stat.volume + value,
      mints: stat.mints + (from === ZERO ? 1 : 0),
      burns: stat.burns + (to === ZERO ? 1 : 0),
    });
  },
);
