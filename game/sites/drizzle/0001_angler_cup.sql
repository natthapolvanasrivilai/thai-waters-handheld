CREATE TABLE `cup_entries` (
	`day` integer NOT NULL,
	`angler` text NOT NULL,
	`best` integer NOT NULL,
	PRIMARY KEY(`day`, `angler`)
);
