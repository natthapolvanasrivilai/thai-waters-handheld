CREATE TABLE `event_players` (
	`round` integer NOT NULL,
	`spot` integer NOT NULL,
	`player` text NOT NULL,
	`score` integer NOT NULL,
	`seen` integer NOT NULL,
	PRIMARY KEY(`round`, `spot`, `player`)
);
