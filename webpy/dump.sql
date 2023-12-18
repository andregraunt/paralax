BEGIN TRANSACTION;
CREATE TABLE chat_messages (
    name text,
    message text
);
INSERT INTO "chat_messages" VALUES('ygyg','ok');
INSERT INTO "chat_messages" VALUES('s','ok ok');
COMMIT;
