-- Drop and recreate the database
DROP DATABASE IF EXISTS culture_music;
CREATE DATABASE culture_music;
USE culture_music;

CREATE TABLE donors (
    donor_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    email VARCHAR(100),
    phone VARCHAR(20)
);


-- TODO: create table users/accounts

-- TODO: create table posts

-- Execute after users/accounts table is created
CREATE TABLE reports (
    report_id INT AUTO_INCREMENT PRIMARY KEY,
    post_id INT NOT NULL,
	report_type ENUM(
    'Misleading information',
    'Inappropriate content',
    'Spam',
    'Fake News',
    'Other'
	) DEFAULT 'Other',
	report_status ENUM('For Review', 'Action Taken', 'No Action') DEFAULT 'For Review',
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    reviewed_by INT,
	FOREIGN KEY (reviewed_by) REFERENCES users(users_id)  ON DELETE SET NULL,
    FOREIGN KEY (post_id) REFERENCES posts(post_id)  ON DELETE CASCADE
);



-- TODO: create table campaigns

-- TODO: create table tiers

-- Execute this after the campaigns and tiers tables are created due to foreign key dependency
CREATE TABLE donations (
    donation_id INT AUTO_INCREMENT PRIMARY KEY,
    notes TEXT,
    receipt_id VARCHAR(100) NOT NULL,
    payment_type VARCHAR(50) NOT NULL,
    donor_id INT,
    campaign_id INT NOT NULL,
    tier_id INT,
    amount FLOAT,
    isAnonymous BOOLEAN,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (donor_id) REFERENCES donors(donor_id)  ON DELETE SET NULL,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id)  ON DELETE NO ACTION,
    FOREIGN KEY (tier_id) REFERENCES tiers(tier_id)  ON DELETE SET NULL
);








