// Both hosts use the same Bangkok calendar, stock limits and ranking rules.
const cupDayMs = 86400000, bangkokOffset = 7 * 3600000;
export function dailyCup(now, spots, stock) {
  const day = Math.floor((now + bangkokOffset) / cupDayMs);
  const spot = (day * 37) % spots.length;
  const candidates = stock.filter(f => f.site === spots[spot].pool);
  const fish = candidates[(Math.floor(day / spots.length) + day * 7) % candidates.length];
  return {day, spot, species:fish.id, name:fish.name, location:spots[spot].name,
    minimum:Math.ceil(fish.low + (fish.high - fish.low) * .45), maximum:fish.high,
    closes:(day + 1) * cupDayMs - bangkokOffset};
}
export async function tournament(db, angler, report, spots, stock, now = Date.now()) {
  const goal = dailyCup(now, spots, stock);
  const {day, spot, species, cm, action} = report || {};
  if (!['view','join','file'].includes(action)) return {error:'Unknown action'};
  const statements = [];
  const query = (sql,...values) => db.prepare(sql).bind(...values);
  let accepted = false;
  if (action === 'join' && day === goal.day) {
    statements.push(query('INSERT OR IGNORE INTO cup_entries(day,angler,best) VALUES(?,?,0)',day,angler));
    statements.push(query('DELETE FROM cup_entries WHERE day < ?',day - 7));
  }
  if (action === 'file' && day === goal.day && spot === goal.spot && species === goal.species &&
      Number.isInteger(cm) && cm >= goal.minimum && cm <= goal.maximum) {
    accepted = true;
    statements.push(query('UPDATE cup_entries SET best=max(best,?) WHERE day=? AND angler=?',cm,day,angler));
  }
  statements.push(query('SELECT best FROM cup_entries WHERE day=? AND angler=?',goal.day,angler));
  statements.push(query('SELECT angler,best FROM cup_entries WHERE day=? AND best>0 ORDER BY best DESC,angler LIMIT 10',goal.day));
  statements.push(query('SELECT count(*) AS ahead FROM cup_entries WHERE day=? AND best>(SELECT best FROM cup_entries WHERE day=? AND angler=?)',goal.day,goal.day,angler));
  const result = (await db.batch(statements)).slice(-3);
  const me = result[0].results[0];
  // Only a pseudonym reaches the public results. Session credentials stay private.
  function label(key){let h=2166136261;for(const c of key)h=Math.imul(h^c.charCodeAt(0),16777619);return 'Angler '+(h>>>0).toString(36).toUpperCase().padStart(7,'0');}
  let rank = 0, previous = 0;
  const leaders = result[1].results.map((r,i)=>{
    if(r.best!==previous)rank=i+1;
    previous=r.best;
    return {rank,angler:label(r.angler),cm:r.best,you:r.angler===angler};
  });
  return {goal,angler:label(angler),joined:!!me,accepted:accepted&&!!me,best:me?.best||0,
    rank:me?.best?1+result[2].results[0].ahead:null,leaders};
}
