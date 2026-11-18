const roundMs = 180_000;
const cookieName = 'tw_angler';

function json(value, status = 200, headers = {}) {
  return Response.json(value, {status, headers: {'cache-control': 'no-store', ...headers}});
}

export async function eventResponse(request, db, spotCount, now = Date.now()) {
  if (request.method !== 'POST') return json({error: 'POST required'}, 405, {allow: 'POST'});
  const origin = request.headers.get('origin');
  if (origin && origin !== new URL(request.url).origin) return json({error: 'Invalid origin'}, 403);
  if (request.headers.get('content-type')?.split(';')[0] !== 'application/json') return json({error: 'JSON required'}, 415);
  const text = await request.text();
  if (text.length > 512) return json({error: 'Event report too large'}, 413);
  let report;
  try { report = JSON.parse(text); } catch { return json({error: 'Invalid report'}, 400); }
  const {spot, round, score} = report ?? {};
  if (!Number.isInteger(spot) || spot < 0 || spot >= spotCount || !Number.isInteger(round) ||
      !Number.isSafeInteger(score) || score < 0 || score > 5000) return json({error: 'Invalid report'}, 400);
  const cookie = /(?:^|;\s*)tw_angler=([0-9a-f-]{36})(?:;|$)/.exec(request.headers.get('cookie') || '');
  const id = cookie?.[1] ?? crypto.randomUUID();
  const current = Math.floor(now / roundMs);
  const result = await db.batch([
    db.prepare('DELETE FROM event_players WHERE round < ?').bind(current),
    db.prepare(`INSERT INTO event_players (round, spot, player, score, seen) VALUES (?, ?, ?, ?, ?)
      ON CONFLICT(round, spot, player) DO UPDATE SET score=max(excluded.score,score), seen=max(excluded.seen,seen)`)
      .bind(current, spot, id, round === current ? score : 0, now),
    db.prepare('SELECT count(CASE WHEN seen >= ? THEN 1 END) AS players, sum(score) AS total FROM event_players WHERE round=? AND spot=?')
      .bind(now - 5000, current, spot),
  ]);
  const {players, total} = result[2].results[0];
  const headers = cookie ? {} : {'set-cookie': cookieName + '=' + id + '; Secure; HttpOnly; SameSite=Lax; Path=/event; Max-Age=86400'};
  return json({round: current, spot, seconds: Math.ceil(((current + 1) * roundMs - now) / 1000), players, total, goal: 8}, 200, headers);
}
