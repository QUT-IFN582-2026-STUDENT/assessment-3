-- WARNING: this script DROPS and recreates the tables, so any existing data in them is lost.

CREATE DATABASE IF NOT EXISTS fundraising_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE fundraising_db;

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS donations;
DROP TABLE IF EXISTS posts;
DROP TABLE IF EXISTS tiers;
DROP TABLE IF EXISTS campaigns;
DROP TABLE IF EXISTS accounts;
DROP TABLE IF EXISTS organisations;
DROP TABLE IF EXISTS reports;
SET FOREIGN_KEY_CHECKS = 1;


CREATE TABLE organisations (
    id   INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
	orgType ENUM('Supporter', 'Fundraiser', 'Admin') NOT NULL DEFAULT 'Supporter',
	description TEXT
);

-- accounts: referenced by Campaign.createdBy ("FK to accounts.id")
CREATE TABLE accounts (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(50)  NOT NULL UNIQUE,
	firstName VARCHAR(50) NOT NULL,
    lastName VARCHAR(50) NOT NULL,
    email         VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role          ENUM('Supporter', 'Fundraiser', 'Admin') NOT NULL DEFAULT 'Supporter',
	accountStatus  ENUM('Active', 'Suspended', 'Closed') NOT NULL DEFAULT 'Active',
    orgId         INT NULL,
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (orgId) REFERENCES organisations(id)
);



-- Campaign atrributes according to UML
-- ---------------------------------------------------------------------------
CREATE TABLE campaigns (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    orgId          INT NOT NULL,
    title          VARCHAR(200)  NOT NULL,
    goalAmount     DECIMAL(10,2) NOT NULL,
    amountRaised   DECIMAL(10,2) NOT NULL DEFAULT 0,
    status         ENUM('Pending','Active','Paused','Draft','Closed','Rejected','Suspended') NOT NULL DEFAULT 'Pending',
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
    eventType      ENUM('Free', 'Ticketed') NOT NULL DEFAULT 'Free',
	FOREIGN KEY (orgId)     REFERENCES organisations(id),
    CONSTRAINT fk_campaign_creator FOREIGN KEY (createdBy) REFERENCES accounts(id),
    CONSTRAINT chk_goal_positive   CHECK (goalAmount > 0),
    INDEX idx_campaigns_creator (createdBy)
);

-- Tier attributes according to UML
CREATE TABLE tiers (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    campaignId INT           NOT NULL,
    name       VARCHAR(100)  NOT NULL,
    amount     DECIMAL(10,2) NOT NULL,
    benefits   VARCHAR(500)  NOT NULL DEFAULT '',
    FOREIGN KEY (campaignId) REFERENCES campaigns(id) ON DELETE CASCADE,
    CONSTRAINT chk_tier_amount CHECK (amount > 0)
);

CREATE TABLE posts (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    campaignId INT NOT NULL,
    title       VARCHAR(150) NOT NULL,
    message     TEXT         NOT NULL,
    image_path  VARCHAR(255),
    createdDate  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (campaignId) REFERENCES campaigns(id) ON DELETE CASCADE
    
);


CREATE TABLE reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    postId INT,
	reportType ENUM(
    'Misleading information',
    'Inappropriate content',
    'Spam',
    'Fake News',
    'Other'
	) DEFAULT 'Other',
	reportStatus ENUM('For Review', 'Action Taken', 'No Action') DEFAULT 'For Review',
    createdDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    reviewedBy INT,
	FOREIGN KEY (reviewedBy) REFERENCES accounts(id)  ON DELETE SET NULL,
    FOREIGN KEY (postId) REFERENCES posts(id)  ON DELETE CASCADE
);


CREATE TABLE donations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    notes TEXT,
    receiptId VARCHAR(100) NOT NULL,
    paymentType  ENUM('Credit Card', 'Paypal', 'Google Pay') DEFAULT 'Credit Card',
    accountId INT,
    campaignId INT,
    tierId INT,
    amount  DECIMAL(10,2) NOT NULL,
    isAnonymous TINYINT(1),
    createdDate DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (accountId) REFERENCES accounts(id)  ON DELETE SET NULL,
    FOREIGN KEY (campaignId) REFERENCES campaigns(id)  ON DELETE SET NULL,
    FOREIGN KEY (tierId) REFERENCES tiers(id)  ON DELETE SET NULL
);

-- Add trigger for donations
DROP TRIGGER IF EXISTS trg_donation_insert;
CREATE TRIGGER trg_donation_insert AFTER INSERT ON donations
FOR EACH ROW
    UPDATE campaigns
    SET amountRaised = amountRaised + NEW.amount,
        updatedDate = NOW()
    WHERE id = NEW.campaignId;

-- Insert records
-- organisations
INSERT INTO organisations (id, name, orgType, description) VALUES
(1, 'Pamana in Brisbane', 'Fundraiser',
 'Pamana in Brisbane is an Australian Filipino community driven cultural group dedicated to celebrating and preserving the rich musical, artistic, and traditional heritage of the Filipino people. Rooted in the meaning of pamana—“legacy” or “heritage”—the organisation brings together Filipino families, artists, musicians, dancers, and cultural advocates across Brisbane to showcase the vibrancy of Filipino culture.'),
(2, 'Australian Multicultural Group','Fundraiser',
 'A community-led organisation promoting different culture and arts in Queensland.'),
(3, 'Culture Music', 'Admin','Culture Music is a platform for cultural music fundraising events.'),
(4, 'Supporter','Supporter', 'Event Supporter or Donor'),
(5, 'Not Listed','Fundraiser', 'Organisation not listed');

-- Every accounts below has the password:  Password123!
-- accounts: 3 fundraisers (to prove ownership rules), 5 supporter, 2 admin
INSERT INTO accounts (id, username, firstName, lastName, email, password_hash, role, accountStatus, orgId)
VALUES
(1,'fundraiser1','Olivia','Brown','fundraiser1@example.com',
 'scrypt:32768:8:1$XZOcvuCl3CHtkmHC$cafb9fa4fd7704fba3b8e3fff498da9977dd98e7f5babb930bdfcc6600511538b783736ae9ac3b374364389b2ae97db3f1bf4f2b8bbe347442d284bbceedcf12',
 'Fundraiser','Active',1),
(2,'fundraiser2','Ethan','Clarke','fundraiser2@example.com',
 'scrypt:32768:8:1$XZOcvuCl3CHtkmHC$cafb9fa4fd7704fba3b8e3fff498da9977dd98e7f5babb930bdfcc6600511538b783736ae9ac3b374364389b2ae97db3f1bf4f2b8bbe347442d284bbceedcf12',
 'Fundraiser','Active',2),
(3,'supporter1','Mia','Johnson','supporter1@example.com',
 'scrypt:32768:8:1$XZOcvuCl3CHtkmHC$cafb9fa4fd7704fba3b8e3fff498da9977dd98e7f5babb930bdfcc6600511538b783736ae9ac3b374364389b2ae97db3f1bf4f2b8bbe347442d284bbceedcf12',
 'Supporter','Active',4),
(4,'supporter2','Ava','Thompson','supporter2@example.com',
 'scrypt:32768:8:1$XZOcvuCl3CHtkmHC$cafb9fa4fd7704fba3b8e3fff498da9977dd98e7f5babb930bdfcc6600511538b783736ae9ac3b374364389b2ae97db3f1bf4f2b8bbe347442d284bbceedcf12',
 'Supporter','Active',4),
(5,'admin1','Lucas','Wright','admin1@example.com',
 'scrypt:32768:8:1$XZOcvuCl3CHtkmHC$cafb9fa4fd7704fba3b8e3fff498da9977dd98e7f5babb930bdfcc6600511538b783736ae9ac3b374364389b2ae97db3f1bf4f2b8bbe347442d284bbceedcf12',
 'Admin','Active',3),
(6,'admin2','Harvey','Nguyen','admin2@example.com',
 'scrypt:32768:8:1$XZOcvuCl3CHtkmHC$cafb9fa4fd7704fba3b8e3fff498da9977dd98e7f5babb930bdfcc6600511538b783736ae9ac3b374364389b2ae97db3f1bf4f2b8bbe347442d284bbceedcf12',
 'Admin','Active',3),
(7,'fundraiser3','Sofia','Martinez','fundraiser3@example.com',
 'scrypt:32768:8:1$XZOcvuCl3CHtkmHC$cafb9fa4fd7704fba3b8e3fff498da9977dd98e7f5babb930bdfcc6600511538b783736ae9ac3b374364389b2ae97db3f1bf4f2b8bbe347442d284bbceedcf12',
 'Fundraiser','Suspended',1),
(8,'supporter3','Liam','Reynolds','supporter3@example.com',
 'scrypt:32768:8:1$XZOcvuCl3CHtkmHC$cafb9fa4fd7704fba3b8e3fff498da9977dd98e7f5babb930bdfcc6600511538b783736ae9ac3b374364389b2ae97db3f1bf4f2b8bbe347442d284bbceedcf12',
 'Supporter','Active',4),
(9,'supporter4','Ella','Sanders','supporter4@example.com',
 'scrypt:32768:8:1$XZOcvuCl3CHtkmHC$cafb9fa4fd7704fba3b8e3fff498da9977dd98e7f5babb930bdfcc6600511538b783736ae9ac3b374364389b2ae97db3f1bf4f2b8bbe347442d284bbceedcf12',
 'Supporter','Active',4),
(10,'supporter5','Noah','Mitchell','supporter5@example.com',
 'scrypt:32768:8:1$XZOcvuCl3CHtkmHC$cafb9fa4fd7704fba3b8e3fff498da9977dd98e7f5babb930bdfcc6600511538b783736ae9ac3b374364389b2ae97db3f1bf4f2b8bbe347442d284bbceedcf12',
 'Supporter','Active',4);

-- Campaigns (UML columns)
--   fundraiser1 (accounts 1): 3 active, 1 paused, 1 pending
--   fundraiser2 (accounts 2): 3 active, 1 pending, 1 suspended
--   pending / suspended are admin decisions and must NOT be changeable by the fundraiser
  INSERT INTO campaigns
(orgId, title, goalAmount, amountRaised, status, location,
 eventDate, eventStartTime, eventEndTime,
 overview, description, bannerImageUrl, isFeatured,
 createdBy, createdDate, updatedDate, publishDate, eventType)
VALUES
-- Brisbane -  Fri/Sat/Sun (3 events)
(1, 'Sound of OPM', 7000.00, 0.00, 'Active',
 '52 Costin St, Fortitude Valley QLD 4006','2026-10-23','2026-10-23 14:00:00','2026-10-23 17:00:00',
 'A showcase of Filipino-Australian youth performers.',
 'Funds support stage hire, sound equipment, and youth workshops.',
 'img/clickerhappy-mic-1132528_1920.jpg', 1, 1, NOW() - INTERVAL 2 DAY, NOW() - INTERVAL 1 DAY, NOW() - INTERVAL 1 DAY, 'Free'),
(1, 'Brisbane Harmony Night', 9000.00, 0.00, 'Active',
 '7 Stratton St, Newstead QLD 4006','2026-10-25','2026-10-25 17:00:00','2026-10-25 21:00:00',
 'A multicultural music night celebrating community harmony.',
 'Funds support performers and venue accessibility.',
 'img/thukka-ai-generated-8309769_1920.jpg', 0, 1, NOW() - INTERVAL 2 DAY, NOW() - INTERVAL 1 DAY, NOW() - INTERVAL 1 DAY, 'Free'),
(1, 'Brisbane Folk Fusion', 6000.00, 0.00, 'Paused',
 '312 Brunswick St, Fortitude Valley QLD 4006','2026-10-24','2026-10-24 14:00:00','2026-10-24 21:00:00',
 'A fusion of folk traditions from Southeast Asia.',
 'Funds support cultural instrument rentals and performers.',
 'img/dedy_timbul-gamelan-7852175_1920.jpg', 0, 1, NOW(), NOW(), NULL, 'Ticketed'),
-- Brisbane - This month (2 events)
(1, 'Brisbane Rhythm Festival', 12000.00, 0.00, 'Active',
 'Grey St, South Brisbane QLD 4101',           -- QPAC Cultural Centre
 DATE_ADD(CURDATE(), INTERVAL 1 WEEK),
 DATE_ADD(NOW(), INTERVAL 1 WEEK),
 DATE_ADD(NOW(), INTERVAL 1 WEEK) + INTERVAL 4 HOUR,
 'A festival of traditional and modern rhythms.',
 'Funds support festival logistics and youth participation.',
 'img/pexels-mark-gil-pineda.jpg', 1, 1, NOW() - INTERVAL 3 DAY, NOW() - INTERVAL 2 DAY, NOW() - INTERVAL 2 DAY, 'Free'),
(1, 'Brisbane Cultural Dance Night', 5000.00, 0.00, 'Pending',
 '480 Gregory Terrace, Bowen Hills QLD 4006',  -- The Old Museum
 DATE_ADD(CURDATE(), INTERVAL 1 WEEK),
 DATE_ADD(NOW(), INTERVAL 1 WEEK) + INTERVAL 2 HOUR,
 DATE_ADD(NOW(), INTERVAL 1 WEEK) + INTERVAL 5 HOUR,
 'A night of cultural dances from local communities.',
 'Funds support costumes, choreography, and venue hire.',
 'img/scratsmacker-outdoors-5159662_1920.jpg', 0, 1, NOW(), NOW(), NULL, 'Ticketed'),
-- Gold Coast - TODAY (Active)
(2, 'Rinascita Sonora Night', 8000.00, 0.00, 'Active',
 '135 Bundall Rd, Surfers Paradise QLD 4217',   -- HOTA
 CURDATE(),
 CONCAT(CURDATE(), ' 18:00:00'),
 CONCAT(CURDATE(), ' 21:00:00'),
 'The Rinascita Sonora fundraiser will support a night of live performances celebrating the musical traditions of Italy and its diaspora. Funds will cover artist fees, accessible venue hire, equipment, and free community tickets so that local families can experience and share the music that makes Brisbane special.',
 'Funds support performers and stage equipment.',
 'img/artesitalia-conductor-5157153_1920.jpg', 1, 2,
 NOW(), NOW(), NOW(), 'Free'),
(2, 'Gold Coast Cultural Jam', 6500.00, 0.00, 'Active',
 '23 Hillcrest Parade, Miami QLD 4220',         -- Miami Marketta
 CURDATE(),
 CONCAT(CURDATE(), ' 18:30:00'),
 CONCAT(CURDATE(), ' 21:30:00'),
 'A jam session featuring multicultural artists.',
 'Funds support venue hire and youth performers.',
 'img/pexels-fausto-ferreira.jpg', 0, 2,
 NOW(), NOW(), NOW(), 'Free'),
-- Gold Coast - TODAY (Pending)
(2, 'Gold Coast Heritage Voices', 7000.00, 0.00, 'Suspended',
 '36 Scarborough St, Southport QLD 4215',       -- Southport RSL Events Hall
 CURDATE(),
 CONCAT(CURDATE(), ' 19:00:00'),
 CONCAT(CURDATE(), ' 22:00:00'),
 'A choir event celebrating cultural heritage.',
 'Funds support choir development and equipment.',
 'img/pexels-blue-ox-studio.jpg', 0, 2,
 NOW(), NOW(), NULL, 'Ticketed'),
-- Gold Coast - NEXT WEEK (Active)
(2, 'Gold Coast Cultural Festival', 15000.00, 0.00, 'Active',
 '165 Duringan St, Currumbin QLD 4223',          -- Soundlounge Currumbin
 DATE_ADD(CURDATE(), INTERVAL 1 WEEK),
 DATE_ADD(CURDATE(), INTERVAL 1 WEEK) + INTERVAL 18 HOUR,
 DATE_ADD(CURDATE(), INTERVAL 1 WEEK) + INTERVAL 22 HOUR,
 'A large-scale cultural festival.',
 'Funds support festival logistics and performers.',
 'img/pexels-gabriel-foureaux.jpg', 1, 2,
 NOW(), NOW(), NOW(), 'Free'),
-- Gold Coast - NEXT MONTH (Pending)
(2, 'Gold Coast Dance Celebration', 5500.00, 0.00, 'Pending',
 '1 Casino Dr, Broadbeach QLD 4218',             -- The Star Gold Coast
 DATE_ADD(CURDATE(), INTERVAL 1 MONTH),
 DATE_ADD(CURDATE(), INTERVAL 1 MONTH) + INTERVAL 19 HOUR,
 DATE_ADD(CURDATE(), INTERVAL 1 MONTH) + INTERVAL 22 HOUR,
 'A celebration of cultural dances.',
 'Funds support costumes and choreography.',
 'img/img/timokefoto-african-2771092_1920.jpg', 0, 2,
 NOW(), NOW(), NULL, 'Ticketed'),
-- Sunshine Coast - Next week Tue/Wed/Thu
(1, 'Sunshine Coast Cultural Waves', 6000.00, 0.00, 'Active',
 '114 Sportsmans Parade, Bokarina QLD 4575','2026-10-21','2026-10-21 14:00:00','2026-10-21 21:00:00',
 'A cultural music event by coastal communities.',
 'Funds support performers and youth workshops.',
 'img/pexels-vietfotos-18238104.jpg', 1, 2, NOW() - INTERVAL 2 DAY, NOW() - INTERVAL 1 DAY, NOW() - INTERVAL 1 DAY, 'Free'),
(2, 'Sunshine Coast Harmony Fest', 9000.00, 0.00, 'Active',
 '60 Noosa Dr, Noosa Heads QLD 4567','2026-10-23','2026-10-23 14:00:00','2026-10-23 21:00:00',
 'A multicultural harmony festival.',
 'Funds support venue hire and performers.',
 'img/img/3935302-adult-3169948_1920.jpg', 0, 2, NOW(), NOW(), NOW(), 'Free'),
(1, 'Sunshine Coast Heritage Night', 7000.00, 0.00, 'Pending',
 '20 Minchinton St, Caloundra QLD 4551','2026-10-25','2026-10-24 14:00:00','2026-10-24 21:00:00',
 'A night celebrating cultural heritage.',
 'Funds support cultural instruments and performers.',
 'img/pexels-diego-santos.jpg', 0, 2, NOW(), NOW(), NULL, 'Ticketed'),
-- Sunshine Coast - Next month
(2, 'Sunshine Coast Rhythm Festival', 11000.00, 0.00, 'Active',
 '10/12-20 Ocean St, Maroochydore QLD 4558',     -- Solbar
 DATE_ADD(CURDATE(), INTERVAL 1 MONTH),
 DATE_ADD(NOW(), INTERVAL 1 MONTH),
 DATE_ADD(NOW(), INTERVAL 1 MONTH) + INTERVAL 4 HOUR,
 'A festival of rhythms and cultural performances.',
 'Funds support festival logistics and youth participation.',
 NULL, 1, 2, NOW(), NOW(), NOW(), 'Free'),
(2, 'Sunshine Coast Cultural Dance Night', 5000.00, 0.00, 'Pending',
 '11 Millwell Rd E, Maroochydore QLD 4558',      -- Millwell Road Community Centre
 DATE_ADD(CURDATE(), INTERVAL 1 MONTH),
 DATE_ADD(NOW(), INTERVAL 1 MONTH) + INTERVAL 2 HOUR,
 DATE_ADD(NOW(), INTERVAL 1 MONTH) + INTERVAL 5 HOUR,
 'A cultural dance night featuring local communities.',
 'Funds support costumes and choreography.',
 NULL, 0, 2, NOW(), NOW(), NULL, 'Ticketed');

 

-- Tiers (UML: campaignId, name, amount, benefits)
INSERT INTO tiers (campaignId, name, amount, benefits)
VALUES
-- Campaign 1 (Brisbane)
(1, 'Barkada Supporter', 15.00, 'Digital thank-you card from performers'),
(1, 'OPM Harmony Pass', 40.00, 'Access to exclusive rehearsal clips'),
(1, 'Serenade Circle', 90.00, 'Reserved seating + backstage photo wall'),
(1, 'Platinum OPM Patron', 200.00, 'Meet & greet with headline artists + signed poster'),
-- Campaign 2 (Brisbane)
(2, 'Harmony Supporter', 20.00, 'Digital harmony badge'),
(2, 'Unity Bronze', 55.00, 'Reserved seating + event photo pack'),
(2, 'Symphony Silver', 130.00, 'Priority seating + backstage access'),
(2, 'Harmony Gold Patron', 280.00, 'VIP lounge + signed group photo'),
-- Campaign 3 (Brisbane)
(3, 'Silver',   100.00, 'Name on the garden thank-you board.'),
(3, 'Platinum',250.00, 'A plaque and an invitation to the opening day.'),
-- Campaign 4 (Brisbane)
(4, 'Supporter', 20.00, 'Social media thank-you'),
(4, 'Bronze', 50.00, 'Event shout-out'),
(4, 'Silver', 100.00, 'Priority seating'),
(4, 'Gold', 250.00, 'VIP meet & greet'),
-- Campaign 5 (Brisbane)
(5, 'Bronze',   20.00, 'Name listed on donor wall.'),
(5, 'Silver',   50.00, 'One free community ticket, event updates and name listed on donor wall.'),
(5, 'Gold',    100.00, 'Highlighted name on donor wall, acknowledgement in the event program and two event tickets.'),
(5, 'Platinum',250.00, 'Highlighted name on donor wall, sponsor recognition and four event tickets.'),
-- Campaign 6 (Gold Coast)
(6, 'Cultura Friend', 20.00, 'Name listed on cultural supporters wall'),
(6, 'Sonora Bronze', 60.00, 'Priority entry + souvenir wristband'),
(6, 'Melodia Silver', 120.00, 'Premium seating + artist Q&A access'),
(6, 'Rinascita Gold Patron', 300.00, 'VIP lounge access + signed event program'),
-- Campaign 7 (Gold Coast)
(7, 'Jam Starter', 15.00, 'Exclusive behind-the-scenes mini clip'),
(7, 'Groove Bronze', 50.00, 'Event merch discount + early entry'),
(7, 'Rhythm Silver', 120.00, 'Front-row access + performer shout-out'),
(7, 'Cultural Jam Gold', 300.00, 'VIP pit access + signed drumstick souvenir'),
-- Campaign 8 (Gold Coast)
(8, 'Silver',   50.00, 'Name on the garden thank-you board.'),
(8, 'Platinum',250.00, 'A plaque on a raised bed and an invitation to the opening day.'),
-- Campaign 9 (Gold Coast)
(9, 'Supporter', 20.00, 'Social media thank-you'),
(9, 'Bronze', 50.00, 'Event shout-out'),
(9, 'Silver', 100.00, 'Priority seating'),
(9, 'Gold', 250.00, 'VIP meet & greet'),
-- Campaign 10 (Gold Coast)
(10, 'Supporter', 20.00, 'Social media thank-you'),
(10, 'Bronze', 50.00, 'Event shout-out'),
(10, 'Silver', 100.00, 'Priority seating'),
(10, 'Gold', 250.00, 'VIP meet & greet'),
-- Campaign 11 (Sunshine Coast)
(11, 'Wave Supporter', 18.00, 'Social media shout-out'),
(11, 'Coastal Bronze', 45.00, 'Early venue entry + event sticker pack'),
(11, 'Island Silver', 110.00, 'Front-row seating + performer meet & greet'),
(11, 'Cultural Gold Tide', 260.00, 'VIP seating + exclusive backstage tour'),
-- Campaign 12 (Sunshine Coast)
(12, 'Supporter', 20.00, 'Social media thank-you'),
(12, 'Bronze', 50.00, 'Event shout-out'),
(12, 'Silver', 100.00, 'Priority seating'),
(12, 'Gold', 250.00, 'VIP meet & greet'),
-- Campaign 13 (Sunshine Coast)
(13, 'Supporter', 20.00, 'Social media thank-you'),
(13, 'Bronze', 50.00, 'Event shout-out'),
(13, 'Silver', 100.00, 'Priority seating'),
(13, 'Gold', 250.00, 'VIP meet & greet'),
-- Campaign 14 (Sunshine Coast)
(14, 'Supporter', 20.00, 'Social media thank-you'),
(14, 'Bronze', 50.00, 'Event shout-out'),
(14, 'Silver', 100.00, 'Priority seating'),
(14, 'Gold', 250.00, 'VIP meet & greet'),
-- Campaign 15 (Sunshine Coast)
(15, 'Bronze', 20.00, 'Thank-you message from the garden team.'),
(15, 'Silver',50.00, 'Name on the garden thank-you board.'),
(15, 'Gold', 250.00, 'Priority entry + souvenir wristband'),
(15, 'Platinum',500.00, 'VIP meet & greet.');


-- Donations (triggers update campaigns.amountRaised automatically)
INSERT INTO donations
(notes, receiptId, paymentType, accountId, campaignId, tierId, amount, isAnonymous, createdDate)
VALUES
('Excited to support this cultural night — the lineup looks amazing!',
 'RCP-GC-3001', 'Credit Card', 3, 6, 19, 50.00, 0,
 CONCAT(CURDATE(), ' 18:00:00') - INTERVAL 7 DAY),
('I love the Italian musical heritage. Happy to contribute!',
 'RCP-GC-3002', 'PayPal', 4, 6, 19, 20.00, 1,
 CONCAT(CURDATE(), ' 19:00:00') - INTERVAL 5 DAY),
('Supporting local artists is important — keep the culture alive.',
 'RCP-GC-3003', 'Credit Card', 8, 6, 21, 120.00, 0,
 CONCAT(CURDATE(), ' 18:00:00') - INTERVAL 3 DAY),
('The rehearsals looked incredible. Proud to support this event.',
 'RCP-GC-3004', 'Google Pay', 9, 6, 22, 300.00, 0,
 CONCAT(CURDATE(), ' 17:00:00') - INTERVAL 2 DAY),
('Anonymous donation — wishing everyone a beautiful cultural night.',
 'RCP-GC-3005', 'Credit Card', 10, 6, 20, 60.00, 1,
 CONCAT(CURDATE(), ' 19:30:00') - INTERVAL 1 DAY);


-- Posts for campaignid 2
INSERT INTO posts ( campaignId, title, message, image_path, createdDate)
VALUES
(2, 'Venue Preparation Underway',
 'HOTA is being set up for an unforgettable Rinascita Sonora Night.',
 'img/pexels-violins-1838390_1920.jpg',
 CONCAT(CURDATE(), ' 18:00:00') - INTERVAL 5 DAY),
(2, 'Artist Rehearsals',
 'Our performers delivered an incredible rehearsal — the energy is unreal.',
 'img/yannazazu-orchestra-2098877_1920.jpg',
 CONCAT(CURDATE(), ' 18:00:00') - INTERVAL 2 DAY),
(2, 'Final Technical Check',
 'Sound and lighting checks are complete. Everything is ready for tonight!',
 'img/pexels-vietfotos-18238104.jpg',
 CONCAT(CURDATE(), ' 18:00:00') - INTERVAL 1 DAY);

 
-- Reports for postId 1 & 2
INSERT INTO reports (id, postId, reportType, reportStatus, reviewedBy, createdDate)
VALUES
(1,1, 'Spam', 'For Review', NULL,
 CONCAT(CURDATE(), ' 18:20:00') - INTERVAL 2 DAY),
(2,2, 'Inappropriate content', 'Action Taken', 6,
 CONCAT(CURDATE(), ' 18:30:00') - INTERVAL 1 DAY);

