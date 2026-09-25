"""Compare Arc's two USDC Transfer streams over a block range through HyperSync.

Usage: ENVIO_API_TOKEN=... python3 scripts/compare_usdc_streams.py START END
END is exclusive. The blog sample used 22477236 22577236.
"""
import collections, json, os, sys, urllib.request

TOKEN = os.environ["ENVIO_API_TOKEN"]
URL = "https://arc.hypersync.xyz/query"
SYSTEM = "0xfffffffffffffffffffffffffffffffffffffffe"
ERC20 = "0x3600000000000000000000000000000000000000"
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
ZERO = "0x" + "0" * 64


def query(body):
    req = urllib.request.Request(
        URL,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {TOKEN}"},
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read())


start, end = int(sys.argv[1]), int(sys.argv[2])
logs, block = [], start
while block < end:
    d = query({
        "from_block": block,
        "to_block": end,
        "logs": [{"address": [SYSTEM, ERC20], "topics": [[TRANSFER]]}],
        "field_selection": {"log": ["address", "transaction_hash", "topic1", "topic2", "data"]},
    })
    for batch in d.get("data", []):
        logs += batch.get("logs", [])
    nxt = d.get("next_block")
    if not nxt or nxt <= block:
        break
    block = nxt

value = lambda log: int(log["data"], 16)
system = [l for l in logs if l["address"].lower() == SYSTEM]
erc20 = [l for l in logs if l["address"].lower() == ERC20]

# The ERC-20 stream is 6 decimals and the system stream is 18, so scale by 10**12 to match.
unmatched = collections.Counter(
    (l["transaction_hash"], l["topic1"], l["topic2"], value(l) * 10**12) for l in erc20
)
both = 0
for l in system:
    key = (l["transaction_hash"], l["topic1"], l["topic2"], value(l))
    if unmatched[key]:
        unmatched[key] -= 1
        both += 1

print(f"system Transfer logs:        {len(system):,}")
print(f"ERC-20 Transfer logs:        {len(erc20):,}")
print(f"in both streams:             {both:,} ({both / len(system):.1%} of system)")
print(f"system only:                 {len(system) - both:,} ({(len(system) - both) / len(system):.1%} of system)")
print(f"ERC-20 only (zero or self):  {sum(unmatched.values()):,}")
print(f"finer than 6 decimals:       {sum(1 for l in system if value(l) % 10**12):,}")
print(f"mints / burns:               {sum(1 for l in system if l['topic1'] == ZERO):,} / {sum(1 for l in system if l['topic2'] == ZERO):,}")
