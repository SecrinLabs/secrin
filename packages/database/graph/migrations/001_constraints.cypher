CREATE CONSTRAINT project_guid_unique IF NOT EXISTS
FOR (p:Project)
REQUIRE p.guid IS UNIQUE;

CREATE CONSTRAINT repo_guid_unique IF NOT EXISTS
FOR (r:Repository)
REQUIRE r.guid IS UNIQUE;

CREATE CONSTRAINT commit_guid_unique IF NOT EXISTS
FOR (c:Commit)
REQUIRE c.guid IS UNIQUE;

CREATE CONSTRAINT file_guid_unique IF NOT EXISTS
FOR (f:File)
REQUIRE f.guid IS UNIQUE;

CREATE CONSTRAINT document_guid_unique IF NOT EXISTS
FOR (d:Document)
REQUIRE d.guid IS UNIQUE;

CREATE CONSTRAINT person_guid_unique IF NOT EXISTS
FOR (u:Person)
REQUIRE u.guid IS UNIQUE;

CREATE CONSTRAINT embedding_guid_unique IF NOT EXISTS
FOR (e:EmbeddingRef)
REQUIRE e.guid IS UNIQUE;
