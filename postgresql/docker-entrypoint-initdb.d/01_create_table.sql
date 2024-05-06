/*
 Navicat Premium Data Transfer

 Source Server         : CKAN 192.168.149.160
 Source Server Type    : PostgreSQL
 Source Server Version : 140011 (140011)
 Source Host           : localhost:5432
 Source Catalog        : ckan_default
 Source Schema         : public

 Target Server Type    : PostgreSQL
 Target Server Version : 140011 (140011)
 File Encoding         : 65001

 Date: 22/04/2024 09:22:51
*/


-- ----------------------------
-- Table structure for package_request
-- ----------------------------
DROP TABLE IF EXISTS "public"."package_request";
CREATE TABLE "public"."package_request" (
  "id" text COLLATE "pg_catalog"."default" NOT NULL,
  "notes" text COLLATE "pg_catalog"."default",
  "owner_org" text COLLATE "pg_catalog"."default",
  "modified" timestamp(6),
  "first_name" text COLLATE "pg_catalog"."default",
  "package_name" text COLLATE "pg_catalog"."default",
  "email" text COLLATE "pg_catalog"."default",
  "scope" text COLLATE "pg_catalog"."default",
  "send_data" bool DEFAULT false,
  "objective" text COLLATE "pg_catalog"."default",
  "last_name" text COLLATE "pg_catalog"."default",
  "created" timestamp(6)
)
;
COMMENT ON COLUMN "public"."package_request"."notes" IS 'รายละเอียดชุดข้อมูลที่ต้องการ';
COMMENT ON COLUMN "public"."package_request"."owner_org" IS 'หน่วยงานที่ร้องขอ';
COMMENT ON COLUMN "public"."package_request"."modified" IS 'ระยะเวลาที่ต้องการใช้ข้อมูล';
COMMENT ON COLUMN "public"."package_request"."first_name" IS 'ชื่อ';
COMMENT ON COLUMN "public"."package_request"."package_name" IS 'ชุดที่ร้องขอ';
COMMENT ON COLUMN "public"."package_request"."email" IS 'email';
COMMENT ON COLUMN "public"."package_request"."scope" IS 'ขอบเขตการใช้ข้อมูล';
COMMENT ON COLUMN "public"."package_request"."send_data" IS 'สถานะการส่งข้อมูล f=ยังไม่ได้ส่ง/t=ส่งให้แล้ว';
COMMENT ON COLUMN "public"."package_request"."objective" IS 'วัตถุประสงค์';
COMMENT ON COLUMN "public"."package_request"."last_name" IS 'นามสกุล';
COMMENT ON COLUMN "public"."package_request"."created" IS 'วันที่สร้าง';

-- ----------------------------
-- Primary Key structure for table package_request
-- ----------------------------
ALTER TABLE "public"."package_request" ADD CONSTRAINT "package_copy1_pkey" PRIMARY KEY ("id");

/*
 Navicat Premium Data Transfer

 Source Server         : CKAN 192.168.149.160
 Source Server Type    : PostgreSQL
 Source Server Version : 140011 (140011)
 Source Host           : localhost:5432
 Source Catalog        : ckan_default
 Source Schema         : public

 Target Server Type    : PostgreSQL
 Target Server Version : 140011 (140011)
 File Encoding         : 65001

 Date: 02/05/2024 16:50:18
*/


-- ----------------------------
-- Table structure for ckanext_pages
-- ----------------------------
DROP TABLE IF EXISTS "public"."ckanext_pages";
CREATE TABLE "public"."ckanext_pages" (
  "id" text COLLATE "pg_catalog"."default" NOT NULL,
  "title" text COLLATE "pg_catalog"."default",
  "name" text COLLATE "pg_catalog"."default",
  "content" text COLLATE "pg_catalog"."default",
  "lang" text COLLATE "pg_catalog"."default",
  "order" text COLLATE "pg_catalog"."default",
  "private" bool,
  "group_id" text COLLATE "pg_catalog"."default",
  "user_id" text COLLATE "pg_catalog"."default",
  "publish_date" timestamp(6),
  "page_type" text COLLATE "pg_catalog"."default",
  "created" timestamp(6),
  "modified" timestamp(6),
  "extras" text COLLATE "pg_catalog"."default",
  "count" int4 DEFAULT 0
)
;

-- ----------------------------
-- Primary Key structure for table ckanext_pages
-- ----------------------------
ALTER TABLE "public"."ckanext_pages" ADD CONSTRAINT "ckanext_pages_pkey" PRIMARY KEY ("id");

/*
 Navicat Premium Data Transfer

 Source Server         : CKAN 192.168.149.160
 Source Server Type    : PostgreSQL
 Source Server Version : 140011 (140011)
 Source Host           : localhost:5432
 Source Catalog        : ckan_default
 Source Schema         : public

 Target Server Type    : PostgreSQL
 Target Server Version : 140011 (140011)
 File Encoding         : 65001

 Date: 25/04/2024 10:02:54
*/


-- ----------------------------
-- Table structure for user
-- ----------------------------
DROP TABLE IF EXISTS "public"."user";
CREATE TABLE "public"."user" (
  "id" text COLLATE "pg_catalog"."default" NOT NULL,
  "name" text COLLATE "pg_catalog"."default" NOT NULL,
  "apikey" text COLLATE "pg_catalog"."default",
  "created" timestamp(6),
  "about" text COLLATE "pg_catalog"."default",
  "password" text COLLATE "pg_catalog"."default",
  "fullname" text COLLATE "pg_catalog"."default",
  "email" text COLLATE "pg_catalog"."default",
  "reset_key" text COLLATE "pg_catalog"."default",
  "sysadmin" bool DEFAULT false,
  "activity_streams_email_notifications" bool DEFAULT false,
  "state" text COLLATE "pg_catalog"."default" NOT NULL DEFAULT 'active'::text,
  "plugin_extras" jsonb,
  "image_url" text COLLATE "pg_catalog"."default",
  "phone" varchar(20) COLLATE "pg_catalog"."default",
  "address" text COLLATE "pg_catalog"."default",
  "secret_level" varchar(50) COLLATE "pg_catalog"."default",
  "organization" text COLLATE "pg_catalog"."default"
)
;

-- ----------------------------
-- Indexes structure for table user
-- ----------------------------
CREATE INDEX "idx_user_id" ON "public"."user" USING btree (
  "id" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);
CREATE INDEX "idx_user_name" ON "public"."user" USING btree (
  "name" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);
CREATE INDEX "idx_user_name_index" ON "public"."user" USING btree (
  (
CASE
    WHEN fullname IS NULL OR fullname = ''::text THEN name
    ELSE fullname
END) COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);

-- ----------------------------
-- Uniques structure for table user
-- ----------------------------
ALTER TABLE "public"."user" ADD CONSTRAINT "user_name_key" UNIQUE ("name");

-- ----------------------------
-- Primary Key structure for table user
-- ----------------------------
ALTER TABLE "public"."user" ADD CONSTRAINT "user_pkey" PRIMARY KEY ("id");

