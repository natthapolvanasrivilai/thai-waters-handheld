import {readFile, writeFile, mkdir} from 'node:fs/promises';

const page = await readFile('game.html', 'utf8');
const catalog = JSON.parse(await readFile('locations.json', 'utf8'));
const events = await readFile('event.mjs', 'utf8');
const handler = `
const gamePage = ${JSON.stringify(page)};
export default {
  async fetch(request, env) {
    const {pathname} = new URL(request.url);
    if (pathname === '/event') return eventResponse(request, env.DB, ${catalog.length});
    if ((request.method === 'GET' || request.method === 'HEAD') && pathname === '/') {
      return new Response(request.method === 'HEAD' ? null : gamePage, {headers:{
        'content-type':'text/html; charset=utf-8', 'cache-control':'private, no-cache',
        'permissions-policy':'accelerometer=(self), gyroscope=(self)'
      }});
    }
    return new Response('Page unavailable', {status:404});
  }
};`;
await mkdir('dist/server', {recursive:true});
await writeFile('dist/server/index.js', events + handler);
