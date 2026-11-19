import {sqliteTable, integer, text, primaryKey} from 'drizzle-orm/sqlite-core';

export const eventPlayers = sqliteTable('event_players', {
  round: integer('round').notNull(),
  spot: integer('spot').notNull(),
  player: text('player').notNull(),
  score: integer('score').notNull(),
  seen: integer('seen').notNull(),
}, table => [primaryKey({columns: [table.round, table.spot, table.player]})]);

export const cupEntries = sqliteTable('cup_entries', {
  day: integer('day').notNull(),
  angler: text('angler').notNull(),
  best: integer('best').notNull(),
}, table => [primaryKey({columns: [table.day, table.angler]})]);
