USE culture_music;

INSERT INTO donors
( donor_id, first_name, last_name, email, phone) 
VALUES
(1, 'Olivia', 'Brown', 'olivia.brown@example.com', '0412555101'),
(2, 'Ethan', 'Clarke', 'ethan.clarke@example.com', '0423888202'),
(3, 'Mia', 'Johnson', 'mia.johnson@example.com', '0434777303'),
(4, 'Lucas', 'Wright', 'lucas.wright@example.com', '0445666404'),
(5, 'Ava', 'Thompson', 'ava.thompson@example.com', '0456999505');


INSERT INTO reports (post_id, report_type, report_status, reviewed_by)
VALUES
(1, 'Misleading information', 'For Review', NULL),
(2, 'Inappropriate content', 'No Action', 3),
(3, 'Spam', 'Action Taken', 2),
(4, 'Other', 'For Review', NULL);



INSERT INTO donations
(donation_id, notes, receipt_id, payment_type, donor_id, campaign_id, tier_id, amount, isAnonymous)
VALUES
(1, 'I loved seeing young performers share their cultural music. It reminded me of my own childhood traditions, so I’m happy to support this campaign.', 
 'RCP-1001', 'Credit Card', 1, 1, 1, 50.00, 0),
(2, 'The community stage project is amazing. I donated because it gives local artists a real chance to shine and celebrate their heritage.', 
 'RCP-1002', 'PayPal', 2, 2, 2, 75.00, 1),
(3, 'The festival brought so many cultures together. I want to help keep that spirit alive and support future events.', 
 'RCP-1003', 'Credit Card', 3, 3, 1, 120.00, 0),
(4, 'The choir development program was inspiring. The voices, the stories, the unity — it deserves all the support it can get.', 
 'RCP-1004', 'Google Pay', 4, 4, 3, 30.00, 0),
(5, 'I donated because cultural dance night was beautiful. It’s important to preserve these traditions for the next generation.', 
 'RCP-1005', 'Credit Card', 5, 5, 2, 200.00, 1);
 



