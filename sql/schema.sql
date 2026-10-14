-- MySQL schema. The `campaigns` table follows the Campaign UML exactly
-- (column names, types, and foreign keys).
--
-- Run with:  mysql -u root -p < schema.sql
--
-- WARNING: this script DROPS and recreates the tables, so any existing data in them
-- is lost. That is intended while you are developing. Re-run seed.sql afterwards.

CREATE DATABASE IF NOT EXISTS fundraising_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE fundraising_db;

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS donations;
DROP TABLE IF EXISTS posts;
DROP TABLE IF EXISTS campaigns;
DROP TABLE IF EXISTS account;
DROP TABLE IF EXISTS users;          -- old table name, replaced by `account`
DROP TABLE IF EXISTS organisation;
SET FOREIGN_KEY_CHECKS = 1;

-- ---------------------------------------------------------------------------
-- organisation: the group a fundraiser runs campaigns for (Campaign.orgId)
-- ---------------------------------------------------------------------------
CREATE TABLE organisation (
    id   INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- account: referenced by Campaign.createdBy ("FK to account.id")
-- ---------------------------------------------------------------------------
CREATE TABLE account (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(50)  NOT NULL UNIQUE,
    email         VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role          ENUM('supporter', 'fundraiser', 'admin') NOT NULL DEFAULT 'supporter',
    orgId         INT NULL,
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_account_org FOREIGN KEY (orgId) REFERENCES organisation(id)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- Campaign (matches the UML)
--   status: pending / rejected / suspended are administrator decisions.
--           A fundraiser may only move a campaign between active, paused, closed.
--   amountRaised is kept up to date automatically by the triggers below.
--   Money uses DECIMAL(10,2): the exact equivalent of the UML "float" for currency.
-- ---------------------------------------------------------------------------
CREATE TABLE campaigns (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    orgId          INT NOT NULL,
    title          VARCHAR(200)  NOT NULL,
    goalAmount     DECIMAL(10,2) NOT NULL,
    amountRaised   DECIMAL(10,2) NOT NULL DEFAULT 0,
    status         VARCHAR(20)   NOT NULL DEFAULT 'pending',
    location       VARCHAR(100)  NOT NULL DEFAULT '',
    eventDate      DATE          NULL,
    eventStartTime DATETIME      NULL,
    eventEndTime   DATETIME      NULL,
    overview       VARCHAR(500)  NOT NULL DEFAULT '',
    description    VARCHAR(2000) NOT NULL DEFAULT '',
    bannerImageUrl VARCHAR(255)  NULL,
    isFeatured     TINYINT(1)    NOT NULL DEFAULT 0,
    createdBy      INT           NOT NULL,
    createdDate    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updatedDate    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    publishDate    DATETIME      NULL,
    eventType      VARCHAR(50)   NULL,
    CONSTRAINT fk_campaign_org     FOREIGN KEY (orgId)     REFERENCES organisation(id),
    CONSTRAINT fk_campaign_creator FOREIGN KEY (createdBy) REFERENCES account(id),
    CONSTRAINT chk_goal_positive   CHECK (goalAmount > 0),
    CONSTRAINT chk_status_values   CHECK (status IN
        ('pending', 'active', 'paused', 'closed', 'rejected', 'suspended')),
    INDEX idx_campaigns_creator (createdBy),
    INDEX idx_campaigns_org (orgId)
) ENGINE=InnoDB;

CREATE TABLE posts (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    campaign_id INT NOT NULL,
    title       VARCHAR(150) NOT NULL,
    message     TEXT         NOT NULL,
    image_path  VARCHAR(255) NOT NULL DEFAULT '',
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_post_campaign FOREIGN KEY (campaign_id)
        REFERENCES campaigns(id) ON DELETE CASCADE,
    INDEX idx_posts_campaign (campaign_id)
) ENGINE=InnoDB;

CREATE TABLE donations (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    campaign_id  INT NOT NULL,
    donor_name   VARCHAR(100) NOT NULL DEFAULT 'Anonymous Supporter',
    donor_email  VARCHAR(120) NOT NULL DEFAULT '',
    amount       DECIMAL(10,2) NOT NULL,
    tier_name    VARCHAR(80)  NOT NULL DEFAULT '',
    message      VARCHAR(500) NOT NULL DEFAULT '',
    is_anonymous TINYINT(1)   NOT NULL DEFAULT 0,
    created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_amount_positive CHECK (amount > 0),
    CONSTRAINT fk_donation_campaign FOREIGN KEY (campaign_id)
        REFERENCES campaigns(id) ON DELETE CASCADE,
    INDEX idx_donations_campaign (campaign_id)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- Keep campaigns.amountRaised in sync with the donations table.
-- (updatedDate = updatedDate stops a donation from counting as an "edit".)
-- ---------------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_donation_insert;
DROP TRIGGER IF EXISTS trg_donation_update;
DROP TRIGGER IF EXISTS trg_donation_delete;

CREATE TRIGGER trg_donation_insert AFTER INSERT ON donations
FOR EACH ROW
    UPDATE campaigns
    SET amountRaised = (SELECT COALESCE(SUM(amount), 0) FROM donations
                        WHERE campaign_id = NEW.campaign_id),
        updatedDate = updatedDate
    WHERE id = NEW.campaign_id;

CREATE TRIGGER trg_donation_update AFTER UPDATE ON donations
FOR EACH ROW
    UPDATE campaigns
    SET amountRaised = (SELECT COALESCE(SUM(amount), 0) FROM donations
                        WHERE campaign_id = NEW.campaign_id),
        updatedDate = updatedDate
    WHERE id = NEW.campaign_id;

CREATE TRIGGER trg_donation_delete AFTER DELETE ON donations
FOR EACH ROW
    UPDATE campaigns
    SET amountRaised = (SELECT COALESCE(SUM(amount), 0) FROM donations
                        WHERE campaign_id = OLD.campaign_id),
        updatedDate = updatedDate
    WHERE id = OLD.campaign_id;