-- ----------------------------
-- Sequence structure for messages_aggregated_id_seq
-- ----------------------------
DROP SEQUENCE IF EXISTS "public"."messages_aggregated_id_seq";
CREATE SEQUENCE "public"."messages_aggregated_id_seq" 
INCREMENT 1
MINVALUE  1
MAXVALUE 2147483647
START 1
CACHE 1;

-- ----------------------------
-- Sequence structure for messages_id_seq
-- ----------------------------
DROP SEQUENCE IF EXISTS "public"."messages_id_seq";
CREATE SEQUENCE "public"."messages_id_seq" 
INCREMENT 1
MINVALUE  1
MAXVALUE 2147483647
START 1
CACHE 1;

-- ----------------------------
-- Table structure for messages
-- ----------------------------
DROP TABLE IF EXISTS "public"."messages";
CREATE TABLE "public"."messages" (
  "id" int4 NOT NULL GENERATED ALWAYS AS IDENTITY (
INCREMENT 1
MINVALUE  1
MAXVALUE 2147483647
START 1
CACHE 1
),
  "msg_id" int8,
  "sender_id" varchar(255) COLLATE "pg_catalog"."default",
  "sender_name" varchar(255) COLLATE "pg_catalog"."default",
  "chat_id" varchar(255) COLLATE "pg_catalog"."default",
  "chat_name" varchar(255) COLLATE "pg_catalog"."default",
  "message" text COLLATE "pg_catalog"."default",
  "date" timestamp(6),
  "is_bot" varchar(5) COLLATE "pg_catalog"."default"
)
;

-- ----------------------------
-- Table structure for messages_aggregated
-- ----------------------------
DROP TABLE IF EXISTS "public"."messages_aggregated";
CREATE TABLE "public"."messages_aggregated" (
  "id" int4 NOT NULL GENERATED ALWAYS AS IDENTITY (
INCREMENT 1
MINVALUE  1
MAXVALUE 2147483647
START 1
CACHE 1
),
  "chat_id" varchar(255) COLLATE "pg_catalog"."default",
  "chat_name" varchar(255) COLLATE "pg_catalog"."default",
  "aggregated_date" date NOT NULL,
  "messages" text COLLATE "pg_catalog"."default" NOT NULL,
  "ai_summary" text COLLATE "pg_catalog"."default"
)
;

-- ----------------------------
-- Alter sequences owned by
-- ----------------------------
ALTER SEQUENCE "public"."messages_aggregated_id_seq"
OWNED BY "public"."messages_aggregated"."id";
SELECT setval('"public"."messages_aggregated_id_seq"', 3, true);

-- ----------------------------
-- Alter sequences owned by
-- ----------------------------
ALTER SEQUENCE "public"."messages_id_seq"
OWNED BY "public"."messages"."id";
SELECT setval('"public"."messages_id_seq"', 2, true);

-- ----------------------------
-- Primary Key structure for table messages
-- ----------------------------
ALTER TABLE "public"."messages" ADD CONSTRAINT "messages_pkey" PRIMARY KEY ("id");

-- ----------------------------
-- Uniques structure for table messages_aggregated
-- ----------------------------
ALTER TABLE "public"."messages_aggregated" ADD CONSTRAINT "unique_chat_id_date" UNIQUE ("chat_id", "aggregated_date");

-- ----------------------------
-- Primary Key structure for table messages_aggregated
-- ----------------------------
ALTER TABLE "public"."messages_aggregated" ADD CONSTRAINT "aggregated_messages_pkey" PRIMARY KEY ("id");
