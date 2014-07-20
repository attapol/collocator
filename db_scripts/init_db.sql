CREATE TABLE Words
(
	WID integer PRIMARY KEY AUTOINCREMENT,
	Word varchar(255),
	WPOS varchar(255),
	DepType varchar(255),
	DepCount integer,
	GovernorCount integer
);
CREATE INDEX WordIndex ON Words(Word);

CREATE TABLE DependencyRelations
(
	GovernorID integer REFERENCES Words(WID),
	IntermediateID integer REFERENCES Words(WID),
	DependentID integer REFERENCES Words(WID),
	GovernorPosition integer,
	DependentPosition integer,
	Count integer
);

