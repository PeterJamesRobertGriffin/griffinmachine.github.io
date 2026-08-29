const headers = {
  "Content-Type": "application/json; charset=utf-8",
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, PUT, OPTIONS",
  "Access-Control-Allow-Headers": "Authorization, Content-Type",
  "Cache-Control": "no-store",
};
const respond = (body, status = 200) => new Response(JSON.stringify(body), { status, headers });

function tokensMatch(supplied, expected) {
  if (typeof supplied !== "string" || typeof expected !== "string") return false;
  let difference = supplied.length ^ expected.length;
  for (let i = 0; i < Math.max(supplied.length, expected.length); i += 1) {
    difference |= (supplied.charCodeAt(i) || 0) ^ (expected.charCodeAt(i) || 0);
  }
  return difference === 0;
}

export default {
  fetch(request, env) {
    if (new URL(request.url).pathname !== "/rarity") return respond({ error: "Not found" }, 404);
    return env.RARITY_STATE.get(env.RARITY_STATE.idFromName("family-guy-r1")).fetch(request);
  },
};

export class RarityState {
  constructor(state, env) { this.state = state; this.env = env; }

  async fetch(request) {
    if (request.method === "OPTIONS") return new Response(null, { headers });
    if (request.method === "GET") {
      const rareChance = (await this.state.storage.get("rareChance")) ?? 0;
      return respond({ family_guy: { rareChance } });
    }
    if (request.method !== "PUT") return respond({ error: "Method not allowed" }, 405);
    const token = request.headers.get("Authorization")?.replace(/^Bearer\s+/i, "");
    if (!tokensMatch(token, this.env.RARITY_WRITE_TOKEN)) return respond({ error: "Unauthorized" }, 401);
    let payload;
    try { payload = await request.json(); } catch { return respond({ error: "Invalid JSON" }, 400); }
    if (payload?.rareChance !== 0 && payload?.rareChance !== 1) {
      return respond({ error: "rareChance must be 0 or 1" }, 400);
    }
    await this.state.storage.put("rareChance", payload.rareChance);
    return respond({ family_guy: { rareChance: payload.rareChance } });
  }
}
