-- Sample data for testing the Campaign Management Page.
-- Run AFTER schema.sql:   mysql -u root -p fundraising_db < seed.sql
--
-- Every account below has the password:  Password123!
-- (Werkzeug scrypt hash, so check_password_hash() accepts it)
-- campaigns.amountRaised is filled in automatically by the donation triggers.

USE fundraising_db;

SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE donations;
TRUNCATE TABLE posts;
TRUNCATE TABLE campaigns;
TRUNCATE TABLE account;
TRUNCATE TABLE organisation;
SET FOREIGN_KEY_CHECKS = 1;

-- ---------------------------------------------------------------------------
-- Organisations
-- ---------------------------------------------------------------------------
INSERT INTO organisation (id, name) VALUES
(1, 'Pamana Filipino in Brisbane'),
(2, 'Ipswich Community Garden Collective');

-- ---------------------------------------------------------------------------
-- Accounts: two fundraisers (to prove ownership rules), one supporter, one admin
-- ---------------------------------------------------------------------------
INSERT INTO account (id, username, email, password_hash, role, orgId) VALUES
(1, 'fundraiser1', 'fundraiser1@example.com',
 'scrypt:32768:8:1$XZOcvuCl3CHtkmHC$cafb9fa4fd7704fba3b8e3fff498da9977dd98e7f5babb930bdfcc6600511538b783736ae9ac3b374364389b2ae97db3f1bf4f2b8bbe347442d284bbceedcf12',
 'fundraiser', 1),
(2, 'fundraiser2', 'fundraiser2@example.com',
 'scrypt:32768:8:1$XZOcvuCl3CHtkmHC$cafb9fa4fd7704fba3b8e3fff498da9977dd98e7f5babb930bdfcc6600511538b783736ae9ac3b374364389b2ae97db3f1bf4f2b8bbe347442d284bbceedcf12',
 'fundraiser', 2),
(3, 'supporter1', 'supporter1@example.com',
 'scrypt:32768:8:1$XZOcvuCl3CHtkmHC$cafb9fa4fd7704fba3b8e3fff498da9977dd98e7f5babb930bdfcc6600511538b783736ae9ac3b374364389b2ae97db3f1bf4f2b8bbe347442d284bbceedcf12',
 'supporter', NULL),
(4, 'admin1', 'admin1@example.com',
 'scrypt:32768:8:1$XZOcvuCl3CHtkmHC$cafb9fa4fd7704fba3b8e3fff498da9977dd98e7f5babb930bdfcc6600511538b783736ae9ac3b374364389b2ae97db3f1bf4f2b8bbe347442d284bbceedcf12',
 'admin', NULL);

-- ---------------------------------------------------------------------------
-- Campaigns (UML columns)
--   fundraiser1 (account 1): one active, one paused
--   fundraiser2 (account 2): one active, one pending, one suspended
--   pending / suspended are admin decisions and must NOT be changeable by the fundraiser
-- ---------------------------------------------------------------------------
INSERT INTO campaigns
    (id, orgId, title, goalAmount, status, location, eventDate, eventStartTime, eventEndTime,
     overview, description, bannerImageUrl, isFeatured, createdBy, publishDate, eventType) VALUES
(1, 1, 'Sound of OPM', 50000.00, 'active', 'The Tivoli, Fortitude Valley',
 '2026-12-05', '2026-12-05 18:00:00', '2026-12-05 21:00:00',
 'Honouring the soul of Filipino music through heartfelt performances and cultural connection.',
 'Funds will pay for performers, sound equipment hire and venue costs for an evening celebrating Original Pilipino Music, and support youth music workshops.',
 NULL, 1, 1, NOW() - INTERVAL 20 DAY, 'Concert'),
(2, 1, 'Youth Instrument Library', 8000.00, 'paused', 'Brisbane, QLD',
 '2027-02-14', '2027-02-14 10:00:00', '2027-02-14 14:00:00',
 'Lending instruments to students who cannot afford them.',
 'We will buy and maintain a library of instruments that local students can borrow for free.',
 NULL, 0, 1, NOW() - INTERVAL 30 DAY, 'Community program'),
(3, 2, 'Community Garden Rebuild', 5000.00, 'active', 'Ipswich, QLD',
 '2026-11-20', '2026-11-20 08:00:00', '2026-11-20 15:00:00',
 'Rebuilding the garden after the floods.',
 'Money raised will replace soil, raised beds and tools destroyed in the flooding.',
 NULL, 0, 2, NOW() - INTERVAL 15 DAY, 'Working bee'),
(4, 2, 'Neighbourhood Library Van', 12000.00, 'pending', 'Logan, QLD',
 '2027-03-08', NULL, NULL,
 'A mobile library for isolated residents.',
 'Purchase and fit out a van that brings books to residents who cannot easily travel.',
 NULL, 0, 2, NULL, 'Community program'),
(5, 2, 'Pop-up Art Studio', 3000.00, 'suspended', 'Gold Coast, QLD',
 '2027-01-17', '2027-01-17 13:00:00', '2027-01-17 16:00:00',
 'Free art workshops for kids.',
 'Hire a space and buy supplies for a series of free after-school art workshops.',
 NULL, 0, 2, NOW() - INTERVAL 25 DAY, 'Workshop');

-- ---------------------------------------------------------------------------
-- Donations (triggers update campaigns.amountRaised automatically)
-- ---------------------------------------------------------------------------
INSERT INTO donations
    (campaign_id, donor_name, donor_email, amount, tier_name, message, is_anonymous, created_at) VALUES
(1, 'Garyn',               'garyn@example.com',  100.00, 'Gold',     'Have so much fun!',        0, NOW() - INTERVAL 10 DAY),
(1, 'Anonymous Supporter', 'anon1@example.com',   50.00, 'Silver',   'Keep the music playing.',  1, NOW() - INTERVAL 8 DAY),
(1, 'Sandy',               'sandy@example.com',  250.00, 'Platinum', 'Supporting local artists.', 0, NOW() - INTERVAL 5 DAY),
(1, 'Chloe Martin',        'chloe@example.com',   20.00, 'Bronze',   '',                          0, NOW() - INTERVAL 5 DAY),
(1, 'Daniel Lee',          'daniel@example.com', 100.00, 'Gold',     '',                          0, NOW() - INTERVAL 2 DAY),
(1, 'Supporter One',       'supporter1@example.com', 50.00, 'Silver', 'Keep it up',               0, NOW() - INTERVAL 1 DAY),
(2, 'Emma Brown',          'emma@example.com',    50.00, 'Silver',   '',                          0, NOW() - INTERVAL 12 DAY),
(2, 'Frank Wilson',        'frank@example.com',  100.00, 'Gold',     'For the kids',              0, NOW() - INTERVAL 6 DAY),
(3, 'Grace Kim',           'grace@example.com',   20.00, 'Bronze',   '',                          0, NOW() - INTERVAL 9 DAY),
(3, 'Henry Adams',         'henry@example.com',  250.00, 'Platinum', 'Rebuild it better!',        0, NOW() - INTERVAL 4 DAY),
(3, 'Anonymous Supporter', 'anon2@example.com',   50.00, 'Silver',   '',                          1, NOW() - INTERVAL 3 DAY),
(5, 'Isla Scott',          'isla@example.com',    20.00, 'Bronze',   '',                          0, NOW() - INTERVAL 15 DAY);

-- ---------------------------------------------------------------------------
-- Posts / updates
-- ---------------------------------------------------------------------------
INSERT INTO posts (campaign_id, title, message, created_at) VALUES
(1, 'Local artists confirmed',
 'We are excited to announce the lineup for the opening night of Sound of OPM.', NOW() - INTERVAL 6 DAY),
(1, 'Community rehearsal day',
 'Thank you to everyone who joined our first community rehearsal.', NOW() - INTERVAL 2 DAY),
(2, 'Instrument donations welcome',
 'We are also accepting second-hand instruments in good condition.', NOW() - INTERVAL 7 DAY),
(3, 'Soil delivery scheduled',
 'The first load of soil arrives next Saturday. Volunteers are welcome.', NOW() - INTERVAL 3 DAY);