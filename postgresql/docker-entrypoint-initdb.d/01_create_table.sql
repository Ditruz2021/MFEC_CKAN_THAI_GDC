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
