-- Migration: add conversation_id to messages_l1 and backfill existing data
ALTER TABLE messages_l1 ADD COLUMN conversation_id TEXT REFERENCES conversations_l2(conversation_id);

CREATE INDEX IF NOT EXISTS idx_messages_l1_conversation_id
    ON messages_l1(conversation_id);

UPDATE messages_l1
SET conversation_id = (
    SELECT c.conversation_id
    FROM conversations_l2 c
    WHERE (messages_l1.sender_phone = c.lead_phone AND messages_l1.receiver_phone = c.secretary_phone)
       OR (messages_l1.sender_phone = c.secretary_phone AND messages_l1.receiver_phone = c.lead_phone)
    LIMIT 1
)
WHERE conversation_id IS NULL;
